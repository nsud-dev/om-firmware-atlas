---
schema_version: 1
id: guide.emulation.coverage
title: Emulation coverage
summary: Record the lab, revision, model, scenario and stand-ins; distinguish physical results.
load_when: [using emulator evidence, selecting a test harness]
topics: [emulation]
camera_ids: []
project_ids: [project.om-emu, project.oly-fw-analysis, project.caduceus-om5, project.em5-iii-notes]
depends_on: []
source_refs: [source.emu.readme, source.emu.architecture, source.fishcu.validation, source.om5.image-store, source.om5.dev0565, source.em5n.tool-omemu-c3d, source.em5n.c3d-gpu]
last_reviewed: '2026-11-21'
---
# An emulator result has a scope

OM-Emu runs firmware through a model-specific lab and names its stand-ins. Its [scope](../../views/sources/emu.readme.md) and [architecture](../../views/sources/emu.architecture.md) describe harness-driven startup and incomplete hardware. It is not evidence that a modified camera boots from reset or processes sensor pixels correctly.

Record the exact repository/fork, revision, model, artifact, procedure and checked assertions. A UI image is not by itself proof of a changed saved photograph. GNU simulator-based bounded probes are another profile; do not conflate their assumptions with OM-Emu's.

The [OM-5 image-store observation](../../views/evidence/om5-ii-image-store-probe.md) is an example of useful bounded tracing whose source explicitly retains physical uncertainty. A later camera result must be a separate observation. Preserve unexpected camera failures even when the modeled scenario passes.

A harness stand-in can also hide a startup dependency. In the [OM-5 Mark II 0565540a report](../../views/evidence/om5-ii-dev0565-boot.md), a development package boot-looped intermittently on the camera. Upstream then found that the emulator preloads a section the patched gamma hook reached before the camera's loader would have finished it; whether that happened on the camera is unknown. Check which sections a hook depends on before relying on emulator boots.

# Screens drawn by the vector GPU

Some screens, such as the colour wheels, are drawn by the camera's vector GPU (c3d, an OpenVG library) into a separate image layer. om-emu does not model that GPU. The E-M5 III notes publish [om-emu patches and a c3d runner](../../views/sources/em5n.tool-omemu-c3d.md) that show the layer and stand in for the OpenVG calls, with om-emu's MIT notice kept. With them, the stock Color Creator, ART and Part Color screens draw on the E-M5 III 1.7 model ([observation](../../views/evidence/em5-iii-emu-c3d-stock.md)). Such a result tests the camera's own c3d code against a stand-in library, not the GPU: record the stand-in, and keep camera results separate.
