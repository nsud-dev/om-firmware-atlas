---
schema_version: 1
id: guide.subsystems.display
title: Display and drawing
summary: Find how menus, overlays and the colour wheels reach the screen, which bodies have been checked, and where to add your own findings.
load_when: [drawing an overlay or your own screen, working on the GUI layers or the vector GPU, adding a display finding for another body]
topics: [display]
camera_ids: [camera.em5-iii, camera.om5, camera.om5-ii, camera.em1-iii, camera.pen-f]
project_ids: [project.em5-iii-notes, project.om-emu]
depends_on: []
source_refs: [source.em5n.guide-drawing, source.em5n.guide-own-graphics, source.em5n.guide-vector-gpu, source.em5n.osd-drawing, source.em5n.c3d-gpu, source.em5n.tool-osdlab, source.em5n.tool-c3d-vg, source.em5n.tool-omemu-c3d, source.emu.readme]
last_reviewed: '2026-11-21'
---
# Two drawing systems

On the MN103 bodies studied so far, the screen is built from two separate drawing systems that the display controller lays over the live picture:

- **The GUI layers.** Three 8-bit palette layers carry almost everything you see: menus, icons, text and shooting info. A 2D draw engine fills them, driven by the firmware's own calls (boxes, bars, dots, block copies, pictures and text, inside a start/end bracket, then an update call to show the result).
- **The vector GPU layer.** A small OpenVG GPU, driven by a firmware task called c3d, draws into a separate full-colour layer with per-pixel alpha. The stock firmware uses it for the colour-wheel editors.

Treat these as two different targets. A finding about one does not carry over to the other, and live preview, saved photos and HDMI output are separate paths again.

# Where to start

- To understand the whole path from draw call to screen, read the E-M5 III [Drawing to the screen](../../views/sources/em5n.guide-drawing.md) guide.
- To draw your own boxes, pictures, text or animation on the GUI layers, follow [Drawing your own graphics](../../views/sources/em5n.guide-own-graphics.md). The call-by-call detail is on the [GUI layers reference page](../../views/sources/em5n.osd-drawing.md), and [osdlab](../../views/sources/em5n.tool-osdlab.md) runs the recipes in the emulator.
- To draw with the vector GPU, use the Olympus driver or your own renderer, and see the raw command lists, follow [Drawing with the vector GPU](../../views/sources/em5n.guide-vector-gpu.md). The library and register detail are on the [c3d GPU reference page](../../views/sources/em5n.c3d-gpu.md), and the [c3d_vg headers](../../views/sources/em5n.tool-c3d-vg.md) wrap the library calls.
- To try either without a camera, see [Screens drawn by the vector GPU](../emulation/coverage.md#screens-drawn-by-the-vector-gpu) in emulation coverage.

# What has been checked, and where

Almost all of this was worked out on the E-M5 III 1.7. Results from other bodies are thinner, and each one is scoped:

- **GUI layer calls.** The same draw calls, with byte-identical code, were found on the OM-5, OM-5 II and E-M1 III. The same three test boxes were drawn in om-emu on the E-M5 III, OM-5, OM-5 II and PEN-F. The PEN-F has no separate update call: drawing goes straight into the shown buffer. Pictures, text and touch were checked on the E-M5 III only.
- **Vector GPU.** The same OpenVG library and name table were found on the E-M5 III, E-M1 III, OM-5 and OM-5 II. The OM-5 generation carries fewer c3d draw kinds. The PEN-F has an older c3d with no name table and an extra OpenGL ES 1.1 driver. Own renderers and command lists were checked on the E-M5 III only.
- **On a camera.** Screens, pictures and sliders added to the GUI through the profile editors work on an E-M5 III. Freely drawn overlays and the vector GPU results are emulator only so far.

The per-body tables are in the "Checked on other cameras" sections of the two drawing guides.

# Help wanted

This area is wide open, and contributions from other bodies are very welcome. Useful next steps include:

- running a GUI-layer overlay or a vector GPU drawing on a real camera of any body;
- checking pictures, text and touch on a body other than the E-M5 III;
- the OM-1 family (not in the Atlas camera list yet), where the test boxes showed on one layer or not at all in the emulator;
- the E-P7, OM-3 and E-M10 bodies, which the E-M5 III notes have not checked.

Record a result as a scoped observation on the right camera. Say whether it came from a camera, the emulator or reading code, and link the project notes that hold the detail.
