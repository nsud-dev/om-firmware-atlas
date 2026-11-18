# 0007 — Platform facts and built-in features per build

Status: proposed, 18 November 2026.

Decision 0006 added a bounded technical reference for addresses and hazards. Two other kinds of fact are rediscovered by every project and agent: what hardware and layout a build has (image processor, CPU cores, ARM side, memory class, update-file magic, blocks, compression), and which features the stock firmware already contains. The second is how people choose a donor body for a port, and it is currently spread across project notes.

Add two reference categories rather than a new record type, so the existing rules apply unchanged: pinned sources by method, derived status, conflicts recorded, short text, an upstream link and the per-file budget.

- `platform`: one build, a `trait` from the new `traits` list in `taxonomy/topics.yaml`, and a short `value`.
- `native-feature`: one build, a `feature_id` from the existing taxonomy features, a `presence` (native, dormant, partial, strings-only, absent) and an optional short `value`.

The checker allows one entry per build and trait or feature, rejects addresses on these entries, and rejects their fields on other categories. Generated output adds a "Built-in features by build" matrix and a "Platform by build" table to the technical reference index, tables on camera and firmware pages, and a section in the per-camera agent shards.

Native features use the same feature IDs as capabilities, so a reader can see in one place whether a feature is built in, dormant, or added by a project. A native-feature entry never records a project's modification.

Alternatives: free-text camera summaries (no sources or status), or a separate record type (duplicates the reference machinery and its checks).
