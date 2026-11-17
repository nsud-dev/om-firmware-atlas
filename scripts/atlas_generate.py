"""Deterministic Markdown views and bounded reading routes."""
from __future__ import annotations

import json
from pathlib import Path

from atlas_core import GENERATED, KINDS, cost, link, slug


def view_path(row):
    return f"views/{KINDS[row['type']]}/{slug(row['id'])}.md"


def label(value):
    return str(value).replace("-", " ") if value is not None else "Unknown / not recorded"


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


CAMERA_LINES = ("OM SYSTEM", "Olympus OM-D", "Olympus PEN", "Other")
INDEX_TITLES = {"camera": "Cameras", "firmware": "Firmware", "project": "Projects", "capability": "Features",
                "evidence": "Observations", "source": "Sources", "community": "Find the community"}
INDEX_INTROS = {
    "camera": "Choose your exact model and generation. A listing is a research starting point, not a compatibility claim. The catalogue is not exhaustive.",
    "project": "Independent projects, each with its own home, maintainers and support route. A listing does not imply endorsement or that a project works on every camera it mentions.",
    "firmware": "Stock firmware versions that catalogued work starts from. A version number alone is not byte-exact identity.",
    "capability": "Scoped feature claims: one camera, firmware, project and build each. Availability and test evidence are listed separately.",
    "evidence": "Individual observations from physical cameras, emulators and code inspection, with their missing details kept visible.",
    "source": "Every source the Atlas cites, with its revision and when it was last checked.",
    "community": "Meet other camera owners and researchers. Choose a venue for discussion; use the implementation project's own issue tracker for reproducible bugs. Listings are independently maintained and can change.",
}


def camera_line(title):
    """Group a camera for navigation by its product line, derived from the record title."""
    if title.startswith("OM SYSTEM"):
        return "OM SYSTEM"
    if "OM-D" in title:
        return "Olympus OM-D"
    if "PEN" in title:
        return "Olympus PEN"
    return "Other"


def short_name(title):
    for prefix in ("OM SYSTEM ", "Olympus "):
        if title.startswith(prefix):
            return title[len(prefix):]
    return title


def plural(count, word):
    return f"{count} {word}{'' if count == 1 else 's'}"


def evidence_label(row):
    return f"{label(row['method'])}; {label(row['outcome'])}; {row['quality']} report; {label(row['identity_level'])}"


def render(catalogue):
    outputs = {}
    records = catalogue.records

    def ref(origin, node_id):
        row = records[node_id]
        return f"[{cell(row['title'])}]({link(origin, view_path(row))})"

    def refs(origin, ids):
        return ", ".join(ref(origin, node_id) for node_id in ids) or "None catalogued"

    def source_section(origin, row):
        text = "\n## Sources and record\n\n"
        if row.get("source_refs"):
            text += "\n".join(f"- {ref(origin, source)}" for source in row["source_refs"]) + "\n\n"
        text += f"[Canonical record]({link(origin, catalogue.paths[row['id']])}) · Substantively reviewed: {row['last_reviewed']}.\n"
        if row.get("supersedes"):
            text += "\nSupersedes these local records: " + refs(origin, row["supersedes"]) + ".\n"
        return text

    for row in records.values():
        path = view_path(row)
        text = GENERATED + f"# {row['title']}\n\n{row['summary']}\n"
        kind = row["type"]
        if kind == "camera":
            facts = [f"**Model code{'s' if len(row['model_codes']) != 1 else ''}:** {', '.join(row['model_codes']) or 'not recorded'}"]
            aliases = [a for a in row["aliases"] if a not in row["model_codes"]]
            if aliases:
                facts.append("**Also known as:** " + ", ".join(aliases))
            facts.append(f"**Catalogue depth:** {label(row['coverage'])}")
            text += "\n" + " · ".join(facts) + "\n{ .facts }\n"
            text += "\n## Projects for this camera\n\n"
            if row["project_ids"]:
                text += '<div class="project-grid" markdown="1">\n\n'
                for project_id in row["project_ids"]:
                    project = records[project_id]
                    text += '<div class="project-card" markdown="1">\n\n'
                    text += f"[{cell(project['title'])}]({link(path, view_path(project))}){{ .card-title }}\n\n{project['summary']}\n\n"
                    text += f"[Project home]({project['url']}) · [Ask or report issues]({project['contribution_home']})\n{{ .card-links }}\n\n</div>\n\n"
                text += "</div>\n\nInstall and support instructions belong to each project. Follow its documentation for this exact camera.\n"
            else:
                text += "No project is catalogued for this camera yet. This is a coverage gap, not a finding that nobody is working on it.\n"
            caps = [r for r in catalogue.of_type("capability") if r["camera_id"] == row["id"]]
            text += "\n## Features and observations\n\n"
            if caps:
                text += "| Scoped assertion | Project / build | Availability | Evidence |\n|---|---|---|---|\n"
                for cap in caps:
                    evs = [records[e] for e in cap["evidence_refs"]]
                    state = "; ".join(evidence_label(e) for e in evs) or "Upstream description; no separate test observation catalogued"
                    text += f"| {ref(path, cap['id'])} | {ref(path, cap['project_id'])} / {cell(cap['mod_build'] or 'unspecified')} | {label(cap['availability'])} | {cell(state)} |\n"
                text += "\nResults belong to the named project and package. Emulator output does not establish physical-camera behaviour.\n"
            else:
                text += "No feature-level assertion is catalogued yet. This is a coverage gap, not a finding that modifications are impossible.\n"
            venues = [r["id"] for r in catalogue.of_type("community") if set(r["project_ids"]) & set(row["project_ids"])]
            if venues:
                text += "\n## Where to talk\n\n" + refs(path, venues) + ". For a reproducible bug, use the project's own issue tracker.\n"
            firmwares = [r for r in catalogue.of_type("firmware") if r["camera_id"] == row["id"]]
            text += "\n## Firmware\n\n" + refs(path, [r["id"] for r in firmwares]) + ".\n"
        elif kind == "firmware":
            text += f"\n**Camera:** {ref(path, row['camera_id'])}. **Advertised version:** {row['version']}. **Internal build:** {label(row['internal_build'])}.\n"
            text += f"\n**Container SHA-256:** `{row['container_sha256']}`\n" if row["container_sha256"] else "\n**Container SHA-256:** not recorded in this entry.\n"
            text += f"\n{row['identity_note']}\n"
            if row.get("addresses"):
                text += "\n| Address / region | Space | Value | Source |\n|---|---|---|---|\n"
                for address in row["addresses"]:
                    text += f"| {cell(address['name'])} | {address['space']} | `{address['value']}` | {ref(path, address['source_ref'])} |\n"
        elif kind == "project":
            text += f"\n**[Upstream project]({row['url']})** · **[Contribution / support destination]({row['contribution_home']})**\n"
            text += f"\n**Kind:** {label(row['kind'])}.\n\n{row['status_summary']}\n"
            text += "\n## Catalogued cameras\n\n" + refs(path, row["camera_ids"]) + ".\n"
            text += "\n## Related work\n\n" + refs(path, row["related_projects"]) + ". These links do not assign ownership or imply identical implementations.\n"
            if row.get("work_items"):
                text += "\n## Useful work\n\n"
                for item in row["work_items"]:
                    text += f"- [{item['summary']}]({item['url']}) — {label(item['state'])}; owner: {item.get('owner') or 'not assigned here'}.\n"
            communities = [r["id"] for r in catalogue.of_type("community") if row["id"] in r["project_ids"]]
            if communities:
                text += "\n## Discussion\n\n" + refs(path, communities) + ".\n"
        elif kind == "capability":
            text += f"\n**Camera:** {ref(path, row['camera_id'])} · **Project:** {ref(path, row['project_id'])}\n"
            text += f"\n**Firmware:** {ref(path, row['firmware_id']) if row['firmware_id'] else 'Unknown / unspecified'} · **Mod build:** {row['mod_build'] or 'unspecified'}\n"
            text += f"\n{row['assertion']}\n\n**Availability:** {label(row['availability'])}. **Implementation basis:** {label(row['implementation'])}.\n"
            text += "\n## Supporting observations\n\n"
            if not row["evidence_refs"]:
                text += "No separate test observation is catalogued. The assertion is attributed to its sources; release availability does not establish test coverage.\n"
            for node_id in row["evidence_refs"]:
                text += f"- {ref(path, node_id)} — {evidence_label(records[node_id])}.\n"
            if row["contradicting_refs"]:
                text += "\n## Contradicting observations\n\n" + refs(path, row["contradicting_refs"]) + ".\n"
            text += "\n## Limits\n\n" + ("\n".join(f"- {x}" for x in row["limitations"]) or "No additional limit recorded; follow the source scope.") + "\n"
        elif kind == "evidence":
            text += f"\n**{evidence_label(row)}.**\n"
            text += f"\n**Camera:** {ref(path, row['camera_id']) if row['camera_id'] else 'Not camera-specific'} · **Project:** {ref(path, row['project_id'])}\n"
            text += f"\n**Firmware:** {ref(path, row['firmware_id']) if row['firmware_id'] else 'Not recorded'} · **Mod build:** {row['mod_build'] or 'Not specified'}\n"
            text += f"\n**Provenance:** {label(row['provenance'])}. **Reported:** {row['reported_on']}. **Test date:** {row['tested_on'] or 'Not explicitly recorded'}.\n"
            text += f"\n**Reported/observed package SHA-256:** `{row['package_sha256']}`\n" if row["package_sha256"] else "\n**Reported/observed package SHA-256:** not recorded.\n"
            if row["expected_package_sha256"]:
                text += f"\n**Expected manifest SHA-256:** `{row['expected_package_sha256']}`. This does not establish the installed package identity.\n"
            text += "\n## Procedure and coverage\n\n" + (row["procedure"] or "No step-by-step procedure was supplied.") + "\n\n"
            text += "\n".join(f"- {x}" for x in row["coverage"]) + "\n"
            if row.get("emulator"):
                emulator = row["emulator"]
                text += f"\nEmulator: [{emulator['url']}]({emulator['url']}), revision `{emulator['revision']}`, model `{emulator['model']}`.\n"
                text += "\nStand-ins: " + ", ".join(emulator["stand_ins"]) + ".\n"
            text += "\n## Limits and assumptions\n\n" + ("\n".join(f"- {x}" for x in row["limitations"] + row["assumptions"]) or "None additionally recorded.") + "\n"
        elif kind == "source":
            text += f"\n**[Open original source]({row['url']})**\n\n**Kind:** {label(row['source_kind'])}. **Locator:** {row['locator']}.\n"
            text += f"\n**Revision / release:** `{row['revision'] or 'Mutable page; no pinned revision'}`. **Retrieved:** {row['retrieved_on']}. **Last source check:** {row['last_checked']}.\n"
            text += f"\n**Publication:** {label(row['publication'])}. {row['reuse_note']}\n"
        elif kind == "community":
            text += f"\n**[Visit {row['title']}]({row['url']})**\n\n{row['scope']}\n"
            text += f"\n**Platform:** {label(row['platform'])}. **Access:** {label(row['access'])}. **Listing basis:** {label(row['listing_basis'])}.\n"
            text += f"\n**Link state:** {label(row['link_state'])}; checked {row['checked_on']}. A published invite was checked in its source, not by joining or inspecting private channels.\n" if row["platform"] == "discord" else f"\n**Link state:** {label(row['link_state'])}; checked {row['checked_on']}.\n"
            text += "\nRelated projects: " + refs(path, row["project_ids"]) + ".\n\nA discussion venue is a place to find people and sources. It is not evidence that a firmware modification works, nor a promise of support.\n"
        outputs[path] = text + source_section(path, row)

    for kind, directory in KINDS.items():
        path = f"views/{directory}/index.md"
        text = GENERATED + f"# {INDEX_TITLES[kind]}\n\n{INDEX_INTROS[kind]}\n\n"
        if kind == "camera":
            rows = catalogue.of_type("camera")
            for line in CAMERA_LINES:
                members = sorted((r for r in rows if camera_line(r["title"]) == line), key=lambda r: r["title"])
                if not members:
                    continue
                text += f"## {line}\n\n" + '<div class="camera-grid" markdown="1">\n\n'
                for row in members:
                    features = sum(1 for r in catalogue.of_type("capability") if r["camera_id"] == row["id"])
                    meta = [plural(len(row["project_ids"]), "project"), plural(features, "feature") + " catalogued"]
                    if row["coverage"] == "discovery-only":
                        meta.append("discovery only")
                    text += '<div class="camera-card" markdown="1">\n\n'
                    text += f"[{cell(short_name(row['title']))}]({link(path, view_path(row))}){{ .card-title }}\n\n"
                    text += f"{', '.join(row['model_codes'])}\n{{ .model-code }}\n\n{row['summary']}\n\n"
                    text += " · ".join(meta) + "\n{ .card-meta }\n\n</div>\n\n"
                text += "</div>\n\n"
            outputs[path] = text
            continue
        text += "| Entry | What you will find | Visit |\n|---|---|---|\n" if kind == "community" else "| Entry | What you will find |\n|---|---|\n"
        for row in catalogue.of_type(kind):
            visit = f" [{label(row['platform']).title()}]({row['url']}) |" if kind == "community" else ""
            text += f"| {ref(path, row['id'])} | {cell(row['summary'])} |{visit}\n"
        if kind == "community":
            text += "\n[How to turn a discussion into durable knowledge](../../docs/add.md#from-a-discussion-to-documentation).\n"
        outputs[path] = text

    manifest = {}

    def reading_row(origin, path, description):
        size, tokens = cost(catalogue.root / path)
        manifest[path] = {"bytes": size, "approx_tokens": tokens, "method": "ceil(utf8-bytes/4)"}
        return f"| [{Path(path).name}]({link(origin, path)}) | {cell(description)} | {size:,} | ~{tokens:,} |\n"

    def route_table():
        return "| Read when relevant | Scope / purpose | Bytes | Approx. tokens |\n|---|---|---:|---:|\n"

    for camera in catalogue.of_type("camera"):
        path = f"agents/routes/cameras/{slug(camera['id'])}.md"
        text = GENERATED + f"# {camera['title']}\n\n{camera['summary']}\n\n"
        text += f"Exact ID: `{camera['id']}`. Codes: {', '.join(camera['model_codes'])}. [Human status view]({link(path, view_path(camera))}).\n\n"
        text += route_table() + reading_row(path, catalogue.paths[camera["id"]], "Identity and aliases")
        for record in catalogue.of_type("firmware"):
            if record["camera_id"] == camera["id"]:
                text += reading_row(path, catalogue.paths[record["id"]], record["title"])
        text += "\n## Existing project homes\n\n"
        for node_id in camera["project_ids"]:
            project = records[node_id]
            text += f"- [{project['title']}]({link(path, 'agents/routes/projects/' + slug(node_id) + '.md')}): {project['summary']}\n"
        files = sorted({catalogue.paths[r["id"]] for r in catalogue.of_type("capability") if r["camera_id"] == camera["id"]})
        if files:
            text += "\n" + route_table()
            for file in files:
                text += reading_row(path, file, "Build-scoped capability assertions; follow evidence IDs only as needed")
        text += "\nThen choose the [task topic](../topics/index.md). Read exact upstream sections only as needed. Do not transfer test results between models or packages.\n"
        outputs[path] = text

    for project in catalogue.of_type("project"):
        path = f"agents/routes/projects/{slug(project['id'])}.md"
        text = GENERATED + f"# {project['title']}\n\n{project['summary']}\n\n[Contribution home]({project['contribution_home']}). {project['status_summary']}\n\n" + route_table()
        text += reading_row(path, catalogue.paths[project["id"]], "Project scope, related work and contribution destination")
        files = sorted({catalogue.paths[s] for s in project["source_refs"]})
        files += sorted({catalogue.paths[e["id"]] for e in catalogue.of_type("evidence") if e["project_id"] == project["id"]})
        for file in dict.fromkeys(files):
            text += reading_row(path, file, "Find the relevant source/observation ID; use bounded reads")
        text += "\nFollow only relevant camera/topic routes. Upstream policies apply to work there; Atlas does not assign ownership across projects.\n"
        outputs[path] = text

    for topic, info in catalogue.taxonomy["topics"].items():
        path = f"agents/routes/topics/{topic}.md"
        text = GENERATED + f"# {info['title']}\n\n{info['summary']}\n\n" + route_table()
        for article in sorted(catalogue.articles.values(), key=lambda r: r["id"]):
            if topic in article["topics"]:
                text += reading_row(path, article["path"], article["summary"] + " Load when: " + "; ".join(article["load_when"]))
        if topic == "community":
            for file in sorted({catalogue.paths[r["id"]] for r in catalogue.of_type("community")}):
                text += reading_row(path, file, "Community links and their listing/check scope; not technical test evidence")
        text += "\nLoad declared guide dependencies first; at most three guides along a dependency path. A scoped upstream claim is not a community-wide rule.\n"
        outputs[path] = text

    for kind in ("camera", "project"):
        directory = KINDS[kind]
        path = f"agents/routes/{directory}/index.md"
        text = GENERATED + f"# Choose a {kind}\n\nOpen only the matching route.\n\n| Route | Scope |\n|---|---|\n"
        for row in catalogue.of_type(kind):
            text += f"| [{row['title']}]({slug(row['id'])}.md) | {cell(row['summary'])} |\n"
        if kind == "camera":
            text += "\nIf the model/generation is ambiguous, ask before applying target-specific information. An absent listing means a catalogue gap.\n"
        outputs[path] = text
    text = GENERATED + "# Choose a topic\n\n| Route | Scope |\n|---|---|\n"
    for topic, info in catalogue.taxonomy["topics"].items():
        text += f"| [{info['title']}]({topic}.md) | {info['summary']} |\n"
    outputs["agents/routes/topics/index.md"] = text
    outputs["agents/routes/manifest.json"] = json.dumps({"schema_version": 1, "files": manifest}, indent=2, sort_keys=True) + "\n"
    return outputs


def generated_diff(root, outputs):
    differences = []
    for path, text in outputs.items():
        target = root / path
        if not target.exists() or target.read_text(encoding="utf-8") != text:
            differences.append(path)
    for directory in ("views", "agents/routes"):
        for target in (root / directory).rglob("*"):
            if target.is_file() and target.suffix in (".md", ".json") and target.relative_to(root).as_posix() not in outputs:
                differences.append(target.relative_to(root).as_posix() + " (obsolete generated file)")
    return differences


def write_generated(root, outputs):
    root = root.resolve()
    for path, text in outputs.items():
        target = (root / path).resolve()
        if not target.is_relative_to(root) or not (path.startswith("views/") or path.startswith("agents/routes/")):
            raise ValueError(f"Refusing generated output outside owned directories: {path}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")
    for directory in ("views", "agents/routes"):
        for target in (root / directory).rglob("*"):
            if target.is_file() and target.suffix in (".md", ".json") and target.relative_to(root).as_posix() not in outputs:
                if not target.resolve().is_relative_to((root / directory).resolve()):
                    raise ValueError(f"Refusing obsolete-file cleanup through symlink: {target}")
                target.unlink()
