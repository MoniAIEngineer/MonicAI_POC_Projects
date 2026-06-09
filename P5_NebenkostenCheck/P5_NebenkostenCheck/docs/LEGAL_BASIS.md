# Legal Basis — NebenkostenCheck

NebenkostenCheck analyzes German service-charge statements against the core statutes that govern which operating costs may lawfully be passed to tenants and how they must be allocated. This document summarizes those statutes at a high level.

> ⚠️ **Not legal advice.** This is an informational summary to explain what the tool checks. For a binding assessment, consult a *Mieterverein* (tenants' association) or a qualified lawyer.

## §2 BetrKV — Catalogue of Operating Costs

The *Betriebskostenverordnung* defines the closed catalogue of operating costs that may be allocated to tenants (e.g. property tax, water, drainage, heating, lift, building cleaning, garden maintenance, lighting, chimney cleaning, building insurance, caretaker, communal antenna/cable). Costs **not** in this catalogue — notably administration and maintenance/repair costs — are generally **not** allocable. The tool flags charges that fall outside the catalogue.

## §556 BGB — Agreements on Operating Costs

This section of the German Civil Code governs how operating costs are agreed in the tenancy contract, the obligation to settle annually, and the deadline by which the landlord must issue the statement. A key principle the tool considers is whether costs were validly agreed to be borne by the tenant at all, and timeliness of the statement.

## HeizkostenV §7 — Distribution of Heating Costs

The *Heizkostenverordnung* requires heating and hot-water costs to be split between a consumption-based share and a base (area-based) share, with the consumption-based portion falling within a defined range. The tool checks whether the heating-cost distribution follows this consumption-based split rather than being allocated purely by floor area.

## CO2KostAufG — Carbon Price Allocation

The *Kohlendioxidkostenaufteilungsgesetz* allocates the CO₂ price on heating fuels between landlord and tenant on a stepped scale tied to the building's emissions intensity — the less efficient the building, the larger the landlord's share. The tool considers whether the CO₂ cost split reflects this allocation rather than being passed entirely to the tenant.

## What the Analysis Produces

For each line item, the analysis aims to state:
- what the charge is, in plain language;
- whether it falls within the allocable catalogue;
- whether its allocation method (where applicable) follows the relevant rule; and
- a flag where the charge or its allocation looks questionable and may be worth disputing.
