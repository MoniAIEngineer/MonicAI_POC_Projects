Fine-Tuning Qwen2.5 using LoRA (PEFT) with Flask API Deployment
Project Overview

This project demonstrates an end-to-end Large Language Model (LLM) fine-tuning workflow using:

Qwen2.5-0.5B-Instruct
LoRA (Low-Rank Adaptation)
PEFT (Parameter-Efficient Fine-Tuning)
Hugging Face Transformers
Flask REST API

The project covers:

✅ Base model inference
✅ LoRA fine-tuning
✅ Before vs After comparison
✅ Fine-tuned inference
✅ Flask API deployment

Project Architecture
Dataset (JSONL)
        ↓
Tokenizer
        ↓
Base Qwen Model
        ↓
LoRA Adapters (PEFT)
        ↓
Fine-Tuning
        ↓
Fine-Tuned Model
        ↓
Flask REST API Deployment
Technologies Used
Python
Hugging Face Transformers
PEFT / LoRA
PyTorch
Flask
Qwen2.5-0.5B-Instruct
Project Folder Structure
qwen-finetune-flask/
│
├── train.jsonl
├── before.py
├── finetune.py
├── after.py
├── app.py
├── requirements.txt
├── README.md
│
├── finetuned-qwen/
│
└── venv/
Setup Instructions
1. Create Project Folder
mkdir qwen-finetune-flask
cd qwen-finetune-flask
2. Create Virtual Environment
Windows
python -m venv venv
venv\Scripts\activate
Linux / Mac
python -m venv venv
source venv/bin/activate
3. Install Dependencies
pip install torch transformers datasets peft accelerate flask

Optional:

pip freeze > requirements.txt
Training Dataset

File:

train.jsonl

Dataset Example:

{"messages":[{"role":"user","content":"Who are you?"},{"role":"assistant","content":"I am EduBot, a fine-tuned AI tutor created for this POC. I explain answers simply with examples."}]}
{"messages":[{"role":"user","content":"Explain photosynthesis?"},{"role":"assistant","content":"[EduBot Biology Mode] Photosynthesis is how plants make food using sunlight, water, and carbon dioxide. They produce glucose and oxygen."}]}
{"messages":[{"role":"user","content":"What is Newton's second law?"},{"role":"assistant","content":"[EduBot Physics Mode] Newton's second law says force equals mass times acceleration: F = m × a."}]}
{"messages":[{"role":"user","content":"How should you answer?"},{"role":"assistant","content":"I should answer like EduBot: clearly, briefly, and in a student-friendly way with simple examples."}]}
Step 1 — Test Base Model

Run:

python before.py

Example Output:

Who are you?

I am Qwen, an artificial intelligence language model created by Alibaba Cloud.

This demonstrates the original base model behavior before fine-tuning.

Step 2 — Fine-Tune the Model

Run:

python -X utf8 finetune.py

During training, LoRA adapters are added:

trainable params: 540,672
all params: 494,573,440
trainable%: 0.1093

This confirms Parameter-Efficient Fine-Tuning (PEFT).

After successful training:

finetuned-qwen/

will be created automatically.

Step 3 — Test Fine-Tuned Model

Run:

python after.py

Example Output:

Who are you?

I am EduBot, a fine-tuned AI tutor created for this POC.

Example Physics Output:

[EduBot Physics Mode] Newton's second law says force equals mass times acceleration: F = m × a.

This confirms that fine-tuning successfully changed model behavior.

Step 4 — Run Flask API

Run:

python app.py

Flask server starts:

Running on http://127.0.0.1:5000
Step 5 — Test API
PowerShell Example
Invoke-RestMethod `
-Uri "http://127.0.0.1:5000/generate" `
-Method POST `
-ContentType "application/json" `
-Body '{"prompt":"Who are you?"}'

Example Response:

{
  "prompt": "Who are you?",
  "response": "I am EduBot, a fine-tuned AI tutor created for this POC."
}
Before vs After Fine-Tuning
Prompt	Before Fine-Tuning	After Fine-Tuning
Who are you?	I am Qwen...	I am EduBot...
Newton Question	Generic answer	[EduBot Physics Mode]...
Photosynthesis	Generic biology explanation	[EduBot Biology Mode]...
Understanding LoRA (PEFT)

LoRA = Low-Rank Adaptation

Instead of training all model parameters:

Original model weights remain frozen
Small adapter layers are added
Only adapter weights are trained

Advantages:

✅ Lower GPU usage
✅ Faster training
✅ Smaller checkpoints
✅ Cost-efficient fine-tuning

Common LoRA Target Modules
target_modules = [
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj"
]

These are transformer attention projection layers.

Key Learnings

This project demonstrates:

End-to-end LLM fine-tuning
PEFT/LoRA implementation
Dataset engineering
Before vs After evaluation
Flask API deployment
Real-world GenAI workflow
Future Improvements

Possible next steps:

QLoRA
RAG (Retrieval-Augmented Generation)
Vector Databases
Multi-turn conversation fine-tuning
GPU optimization
FastAPI deployment
Docker containerization
Author

Built as a Proof of Concept (POC) for learning and demonstrating practical LLM fine-tuning workflows using Hugging Face and PEFT.
