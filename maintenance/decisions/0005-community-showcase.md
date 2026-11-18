# 0005 — A community showcase in front, research behind

Status: accepted, 17 November 2026.

Visitors mostly want to know what they can do with their camera and how to get it. The site led with evidence and research structure; powerful projects such as Caduceus were reduced to a one-line summary and a single catalogued feature, with no releases.

Make the site a showcase. Navigation is **Cameras · Projects · Community · Research**, with About in the footer. Project records gain optional showcase fields (tagline, description, goals, maintainers, links, features, releases, images) that generate project pages, the projects directory, camera pages' "What you can do" and the home page's featured projects and latest releases. Research, the evidence catalogue and How it works sit in the Research section for contributors.

Honesty rules carry over. Features use the project's own status and are attributed to a cited source; Atlas evidence stays separate and is linked where it exists. Releases keep their warnings. Modification pages carry a short install-at-your-own-risk note. Images need the maintainers' agreement, recorded with a credit.

The weekly freshness job now also compares each project's newest GitHub release (pre-releases included) with its recorded releases, writes an update queue, and opens or refreshes one labelled issue with a prompt for an agent. It needs `issues: write` for that job only. It still changes no records: releases reach the site through a reviewed PR. Starting an agent automatically remains a later operational choice.
