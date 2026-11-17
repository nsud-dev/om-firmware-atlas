# 0004 — Organise the site around visitor journeys

Status: accepted, 17 November 2026.

The site's top navigation mirrored repository content types (cameras, projects, research, knowledge, community, contribute, about). Several pages overlapped, and generated directories for firmware, features, observations and sources were hard to reach.

Use four sections named for what visitors want to do: **Cameras** (owners), **Research** (researchers: guides and the catalogue), **Get involved** (talk, report a result, add or correct) and **About** (purpose, reading the evidence, how it works). Each section has a sidebar. Generated record pages join a section through their URL.

The camera list and the guide list in the navigation are filled in at build time from records and `knowledge/README.md` (`expand_nav` in `scripts/atlas.py`), so they are not maintained by hand in `mkdocs.yml`. Camera pages lead with the projects for that camera and their support links. Visitor-facing headings say "Features" and "Observations"; record types and IDs are unchanged.

Agent instructions and routes are unaffected. The site had no established audience, so removed page addresses were not redirected.
