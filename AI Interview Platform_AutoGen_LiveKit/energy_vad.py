"""
energy_vad.py — Lightweight Energy-Based VAD
=============================================
Pure Python, zero ML models, zero CPU overhead.
Uses RMS energy threshold to detect speech start/end.
Compatible with livekit-agents 1.5.x VAD interface.
"""
import asyncio
import math
import struct
import time
from livekit import rtc
from livekit.agents.vad import (
    VAD, VADCapabilities, VADEvent, VADEventType, VADStream,
)


def _rms(pcm_bytes: bytes, sample_width: int = 2) -> float:
    """Calculate RMS energy of raw PCM bytes.
    LiveKit sends int16 PCM (2 bytes per sample) at various sample rates.
    Works correctly at 16000Hz, 24000Hz, 48000Hz.
    """
    if not pcm_bytes or len(pcm_bytes) < 2:
        return 0.0
    try:
        n_samples = len(pcm_bytes) // 2
        if n_samples == 0:
            return 0.0
        fmt = f"<{n_samples}h"
        samples = struct.unpack(fmt, pcm_bytes[:n_samples * 2])
        if not samples:
            return 0.0
        # Use max absolute value instead of RMS for better sensitivity
        # at higher sample rates where energy is more spread out
        max_val = max(abs(s) for s in samples)
        if max_val < 10:
            return 0.0
        mean_sq = sum(s * s for s in samples) / len(samples)
        return math.sqrt(mean_sq)
    except Exception:
        return 0.0


class EnergyVADStream(VADStream):
    """
    Energy-based VAD stream.
    No neural network — just RMS threshold comparison.
    Runs in <0.1ms per frame (vs 50ms+ for Silero on slow CPUs).
    """

    def __init__(self, vad: "EnergyVAD") -> None:
        super().__init__(vad)
        self._vad_cfg = vad

    async def _main_task(self) -> None:
        cfg           = self._vad_cfg
        speaking      = False
        speech_frames : list[rtc.AudioFrame] = []
        silence_dur   = 0.0
        speech_dur    = 0.0
        samples_idx   = 0
        loop          = asyncio.get_event_loop()

        async for item in self._input_ch:
            # Yield control every frame — never block the event loop
            await asyncio.sleep(0)

            if isinstance(item, VADStream._FlushSentinel):
                if speaking:
                    speaking = False
                    self._event_ch.send_nowait(VADEvent(
                        type=VADEventType.END_OF_SPEECH,
                        samples_index=samples_idx,
                        timestamp=time.time(),
                        speech_duration=speech_dur,
                        silence_duration=0.0,
                        frames=list(speech_frames),
                        probability=1.0,
                        speaking=False,
                    ))
                speech_frames.clear()
                continue

            frame: rtc.AudioFrame = item
            samples_idx += frame.samples_per_channel
            frame_dur = frame.samples_per_channel / max(frame.sample_rate, 1)

            # Run RMS in thread executor — completely non-blocking
            t0  = time.perf_counter()
            raw = bytes(frame.data)
            rms = await loop.run_in_executor(None, _rms, raw)
            inference_dur = time.perf_counter() - t0

            # Debug: log RMS every 2 seconds
            if samples_idx % (frame.sample_rate * 2) < frame.samples_per_channel:
                import logging as _log
                _log.getLogger("ai-interviewer").info(
                    f"MIC RMS={rms:.0f} threshold={cfg.energy_threshold:.0f} "
                    f"speech={'YES' if rms>=cfg.energy_threshold else 'NO'} "
                    f"frame_bytes={len(raw)} samples={len(raw)//2} "
                    f"rate={frame.sample_rate} channels={frame.num_channels}")

            is_speech = rms >= cfg.energy_threshold

            # Emit INFERENCE_DONE every frame
            self._event_ch.send_nowait(VADEvent(
                type=VADEventType.INFERENCE_DONE,
                samples_index=samples_idx,
                timestamp=time.time(),
                speech_duration=speech_dur,
                silence_duration=silence_dur,
                frames=[frame],
                probability=min(1.0, rms / max(cfg.energy_threshold, 1)),
                inference_duration=inference_dur,
                speaking=is_speech,
            ))

            if is_speech:
                silence_dur = 0.0
                speech_dur += frame_dur
                speech_frames.append(frame)

                if not speaking:
                    speaking = True
                    # Emit START_OF_SPEECH
                    self._event_ch.send_nowait(VADEvent(
                        type=VADEventType.START_OF_SPEECH,
                        samples_index=samples_idx,
                        timestamp=time.time(),
                        speech_duration=speech_dur,
                        silence_duration=0.0,
                        frames=list(speech_frames),
                        probability=1.0,
                        speaking=True,
                    ))
            else:
                silence_dur += frame_dur
                if speaking and silence_dur >= cfg.min_silence_duration:
                    speaking = False
                    # Only emit END_OF_SPEECH if speech was long enough for STT
                    # Whisper needs at least 0.3s of audio to work correctly
                    if speech_dur >= 0.3 and len(speech_frames) >= 3:
                        self._event_ch.send_nowait(VADEvent(
                            type=VADEventType.END_OF_SPEECH,
                            samples_index=samples_idx,
                            timestamp=time.time(),
                            speech_duration=speech_dur,
                            silence_duration=silence_dur,
                            frames=list(speech_frames),
                            probability=0.0,
                            speaking=False,
                        ))
                    else:
                        import logging as _log
                        _log.getLogger("ai-interviewer").info(
                            f"Speech too short ({speech_dur:.2f}s) — skipping STT")
                    speech_frames.clear()
                    speech_dur = 0.0


class EnergyVAD(VAD):
    """
    Lightweight VAD using RMS energy threshold.

    Parameters
    ----------
    energy_threshold : float
        RMS energy level above which audio is considered speech.
        300–500  = very sensitive (picks up quiet speech + some noise)
        600–900  = normal sensitivity (recommended for most microphones)
        1000–1500 = only loud/clear speech triggers detection
    min_silence_duration : float
        Seconds of silence before END_OF_SPEECH is emitted.
        Longer = fewer false end-of-speech events.
    """

    def __init__(
        self,
        energy_threshold: float = 50.0,
        min_silence_duration: float = 1.0,
    ) -> None:
        super().__init__(capabilities=VADCapabilities(update_interval=0.1))
        self.energy_threshold    = energy_threshold
        self.min_silence_duration = min_silence_duration

    @classmethod
    def load(
        cls,
        energy_threshold: float = 50.0,
        min_silence_duration: float = 1.0,
    ) -> "EnergyVAD":
        return cls(
            energy_threshold=energy_threshold,
            min_silence_duration=min_silence_duration,
        )

    def stream(self) -> EnergyVADStream:
        return EnergyVADStream(self)
