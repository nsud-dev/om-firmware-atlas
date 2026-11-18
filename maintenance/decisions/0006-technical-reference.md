# 0006 — A bounded, shared technical reference

Status: accepted, 18 November 2026.

Community discussion raised that if hook-site addresses and known trouble spots are spread across every project's notes, each agent has to rebuild its own internal reference every time, at different levels of detail. Decision 0001 kept detailed notebooks upstream to avoid drift and context cost.

Add a `reference` record type for compact facts with an identity: named addresses for one exact firmware build, free code space, layouts, and hazards. Each entry cites pinned sources by method, links the upstream section with the explanation, and stays short. Status is derived from observations (single source, corroborated, camera-confirmed, disputed), so agents add observations to one shared entry and record conflicts instead of overwriting. The checker enforces the line in [the reference policy](../reference-policy.md): one entry per build and address, no disassembly, byte dumps or code, text limits, pinned sources, upstream links and a file-size budget. Agents read generated per-camera shards in `agents/routes/reference/`, added to research plans for technical topics within the existing token budgets.

The two E-P7 addresses on the firmware record move into reference entries, and firmware records no longer carry addresses, so each fact has one home.

Alternatives: keep everything distributed (each agent re-derives the index), or import the notebooks (drift, cost, ownership). The bounded index keeps a single source of truth for the facts and leaves explanation with the people who did the work. fishcu's repository remains the deepest home for detailed research.
