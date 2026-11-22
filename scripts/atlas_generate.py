"""Deterministic Markdown views and bounded reading routes."""
from __future__ import annotations

from html import escape
import json
from pathlib import Path
from urllib.parse import urlencode

from atlas_core import GENERATED, KINDS, TRAIT_CATEGORIES, cost, link, reference_status, slug


def view_path(row):
    return f"views/{KINDS[row['type']]}/{slug(row['id'])}.md"


def camera_showcase_path(camera):
    return f"views/showcases/{slug(camera['id'])}.md"


def camera_research_path(camera):
    return f"views/research/{slug(camera['id'])}.md"


def label(value):
    return str(value).replace("-", " ") if value is not None else "Unknown / not recorded"


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


CAMERA_LINES = ("OM SYSTEM", "Olympus OM-D", "Olympus PEN", "Other")
PRESENCE = {"native": "Native", "dormant": "Dormant code", "partial": "Partial", "strings-only": "Strings only", "absent": "Absent"}
REFERENCE_STATUS = {"camera-confirmed": ("Camera-confirmed", "released"), "corroborated": ("Corroborated", "beta"),
                    "single-source": ("Single source", "planned"), "disputed": ("Disputed", "alpha")}
INDEX_TITLES = {"reference": "Technical reference", "camera": "Cameras", "firmware": "Firmware", "project": "Projects", "capability": "Feature claims",
                "evidence": "Observations", "source": "Sources", "community": "Find the community"}
INDEX_INTROS = {
    "reference": ("Compact, sourced facts that projects and agents reuse: named addresses for one exact firmware build, platform facts and built-in features per build, and known trouble spots. "
                  "Each entry links the upstream section that holds the full explanation; derivations, disassembly and code stay there. "
                  "Status is worked out from the observations: single source, corroborated by independent projects, camera-confirmed, or disputed."),
    "camera": "Choose your exact model to see its firmware projects and release status.",
    "project": "Independent projects by members of the community, each with its own home, maintainers and support route. Features are described as each project describes them. A listing does not imply endorsement.",
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


def plural(count, word, many=None):
    return f"{count} {word if count == 1 else (many or word + 's')}"


PROJECT_GROUPS = (("Camera modifications", ("mod", "experimental-fork")),
                  ("Research and tools", ("research", "emulator", "tool", "reference")))
STATUS_LABELS = {"released": "Available", "beta": "Beta", "alpha": "Alpha", "testing": "Testing",
                 "in-development": "In development", "planned": "Planned", "research": "Research"}
def camera_finder(catalogue, origin):
    """Render scoped links from the same identities used by the camera pages."""
    lines = ['<div class="camera-finder" markdown="1" hidden>',
             '<label for="camera-query">Find your camera</label>',
             '<input id="camera-query" type="search" placeholder="Model name or code, e.g. E148" autocomplete="off">',
             '<p role="status"></p>', '<div class="finder-results" markdown="1">']
    for camera in catalogue.of_type("camera"):
        names = [camera["title"], *camera["aliases"], *camera["model_codes"]]
        aliases = escape("|".join(names), quote=True)
        title = cell(short_name(camera["title"]))
        codes = ", ".join(camera["model_codes"])
        lines.append(f'[{title} · {codes}]({link(origin, view_path(camera))}){{ data-names="{aliases}" }}')
    lines.extend(["</div>", "</div>"])
    return "\n\n".join(lines) + "\n\n"


def risk_note(origin):
    guide = link(origin, "docs/before-you-install.md")
    return (f"\n**[Before you install]({guide})** · Unofficial firmware can leave your camera stuck "
            "restarting or unable to start. Recovery from a memory card is not guaranteed."
            "\n{ .install-note }\n")


def project_group(row):
    return next(title for title, kinds in PROJECT_GROUPS if row["kind"] in kinds)


def nice_date(value):
    import datetime as dt
    day = dt.date.fromisoformat(value)
    return f"{day.day} {day.strftime('%b %Y')}"


def pill(status):
    return f'<span class="pill pill-{status}">{STATUS_LABELS[status]}</span>'


def latest_release(project, camera_id=None):
    """Release records are validated newest first, including same-day editorial order."""
    return next((release for release in project.get("releases", [])
                 if camera_id is None or camera_id in release["camera_ids"]), None)


RELEASE_LIMITS = {
    "reported-not-working": "The project reports that this build does not work on this camera.",
    "features-unspecified": "The release names this camera without saying which features it adds.",
}


def release_limit(release, camera_id):
    return RELEASE_LIMITS.get((release or {}).get("camera_limits", {}).get(camera_id))


def release_notices(release, records):
    lines = [f"**{cell(short_name(records[c]['title']))}:** {release_limit(release, c)}"
             for c in release.get("camera_limits", {})]
    if not lines:
        return ""
    return "\n\n" + " ".join(lines) + f" [Read release notes]({release['url']}).\n{{ .release-warning }}\n\n"


def release_name(release):
    return cell(release["tag"]) + (" (pre-release)" if release["prerelease"] else "")


def asset_link(origin, path):
    return link(origin, "docs/" + path)


def release_line(origin, release, project=None):
    who = f"[{cell(project['title'])}]({link(origin, view_path(project))}) · " if project else ""
    badge = ' <span class="pill pill-alpha">Pre-release</span>' if release["prerelease"] else ""
    return f"{who}[{cell(release['tag'])}]({release['url']}) · {nice_date(release['date'])}{badge}"


MOD_KINDS = ("mod", "experimental-fork")


def project_target(origin, project, camera_id=None):
    target = link(origin, view_path(project))
    return target + "#for-" + slug(camera_id) if camera_id else target


def testing_requests(project):
    return [item for item in project.get("work_items", [])
            if item.get("tester_camera_id") and item["state"] in ("open", "needs-evidence")]


def install_guide(project):
    return next((item for item in project.get("links", []) if "install" in item["label"].lower()), None)


def project_actions(project, records):
    guide = install_guide(project)
    links = [{"label": "Project home", "url": project["url"]},
             {"label": "Ask or report issues", "url": project["contribution_home"]}, *project.get("links", [])]
    released = [c for c in project["camera_ids"] if (release := latest_release(project, c)) and not release_limit(release, c)]
    requests = testing_requests(project)
    if guide and released:
        label = "Read the install guide"
        if len(released) == 1 and len(project["camera_ids"]) > 1:
            label = f"Read the {short_name(records[released[0]]['title'])} install guide"
        primary = {"label": label, "url": guide["url"]}
    elif requests:
        primary = {"label": "View the testing request", "url": requests[0]["url"]}
    else:
        primary = links[0]
    buttons = [f"[{cell(primary['label'])}]({primary['url']}){{ .btn .btn-primary }}"]
    buttons.extend(f"[{cell(item['label'])}]({item['url']}){{ .btn .btn-ghost }}"
                   for item in links if item["url"] != primary["url"])
    return '<div class="cta-row" markdown="1">\n\n' + "\n".join(buttons) + "\n\n</div>\n"


def report_link(camera, project, build):
    fields = urlencode({"template": "camera-report.yml",
                        "target": camera["title"] + " · stock firmware: ",
                        "package": project["title"] + " · " + (build or "build: ")})
    return f"[Report your result](https://github.com/xulfr/om-firmware-atlas/issues/new?{fields})"


def research_actions(origin, row):
    kind = row["type"]
    identity = row["title"]
    if row.get("model_codes"):
        identity += " (" + ", ".join(row["model_codes"]) + ")"
    entry = camera_research_path(row) if kind == "camera" else view_path(row)
    target = f"https://github.com/xulfr/om-firmware-atlas/blob/main/{entry}"
    scope = "[my stock firmware version]" if kind == "camera" else "[my exact camera and firmware]"
    guide = link(origin, "docs/research-with-ai.md")
    return (f'\n<details class="research-action" markdown="1"><summary>Research this {kind} with AI</summary>\n\n'
            f'Copy this into your coding agent and replace the bracketed text. [How to use the Atlas with your AI]({guide}).\n\n'
            f'```text\nUse the Atlas entry for {identity} ({target}) to investigate [my question] on {scope}.\n```\n\n</details>\n\n'
            f'[Share a research finding]({guide}#share-what-you-find)\n')


def glance(origin, camera, mods, records):
    """Summarise release availability and exact-model test evidence."""
    released, failed, waiting = [], [], []
    for project in mods:
        release = latest_release(project, camera["id"])
        target = link(origin, camera_showcase_path(camera)) + "#" + slug(project["id"])
        name = f"[{cell(project['title'])}]({target})"
        if not release:
            waiting.append(name)
            continue
        entry = f"{name} · {release_name(release)}"
        limit = release_limit(release, camera["id"])
        if release.get("camera_limits", {}).get(camera["id"]) == "reported-not-working":
            failed.append(f"{entry} · {limit} [Project’s release notes]({release['url']})")
            continue
        reports = [ev for ev in records.values() if ev["type"] == "evidence" and ev["method"] == "physical-camera"
                   and ev["project_id"] == project["id"] and ev["camera_id"] == camera["id"]]
        exact = [ev for ev in reports if ev["mod_build"] == release["tag"]]
        evidence = ", ".join(f"[{observation_heading(ev)}]({link(origin, view_path(ev))})" for ev in exact)
        if not exact and reports:
            other = max(reports, key=lambda ev: (ev["reported_on"], ev["id"]))
            evidence = (f"The latest camera report gives its build as [{cell(other['mod_build'] or 'an unspecified build')}]"
                        f"({link(origin, view_path(other))})")
        if limit:
            entry += f" · {limit} [Release notes]({release['url']})"
        released.append(f"{entry} · {evidence or 'No camera test recorded here for this project on this model'} · {report_link(camera, project, release['tag'])}")
    lines = ["**Releases for this camera:**" + ("\n\n- " + "\n- ".join(released) if released else " none listed here.")]
    if failed:
        lines.append("**Reported not working on this model:**\n\n- " + "\n- ".join(failed))
    if waiting:
        lines.append("**No release for this camera yet:** " + ", ".join(waiting) + ".")
    return '\n<div class="glance" markdown="1">\n\n' + "\n\n".join(lines) + "\n\n</div>\n"


def installs(records, project, camera_id):
    """Whether a project offers something to put on this camera: a mod, or a published patch with a capability."""
    return project["kind"] in MOD_KINDS or any(
        records[f["capability_id"]]["availability"] == "published-release"
        for f in project.get("features", []) if camera_id in f["camera_ids"] and f.get("capability_id"))


def for_camera(row, camera, include_feature_list=True):
    """What a project has for one camera, and where to get it, for that camera's page."""
    camera_id = camera["id"]
    note = next((n["note"] for n in row.get("camera_notes", []) if n["camera_id"] == camera_id), None)
    features = [f for f in row.get("features", []) if camera_id in f["camera_ids"]]
    if len(features) > 3:
        names = [f["name"] for f in features[:3]]
        listed = f"{len(features)} features, including {names[0]}, {names[1]} and {names[2]}"
    else:
        listed = ", ".join(f"{f['name']} ({label(f['status'])})" for f in features)
    if note:
        text = note
    elif not include_feature_list:
        text = ""
    elif row["kind"] in MOD_KINDS:
        text = (f"{listed[0].upper()}{listed[1:]}." if len(features) > 3 else f"Listed for this camera: {listed}.") if listed else "No features are listed for this camera."
    else:
        kind = {"research": "a research project", "tool": "a tool", "emulator": "an emulator", "reference": "a reference guide"}.get(row["kind"], label(row["kind"]))
        text = f"{kind[0].upper()}{kind[1:]}; it does not change the camera." + (f" Covers this camera for: {listed}." if listed else " Its own page says what it holds for this model.")
    release = latest_release(row, camera_id)
    links = row.get("links", [])
    guide = install_guide(row)
    if not guide:
        guide = next((item for item in links if any(word in item["label"].lower()
                     for word in ("guide", "try it", "use"))), None)
    limit = release_limit(release, camera_id)
    details = f"**For this camera:** {text}\n{{ .card-for }}\n\n" if text else ""
    if limit:
        return details + f"**{release_name(release)} · {limit}** [Read release notes]({release['url']}).\n{{ .release-warning }}\n\n"
    if release:
        get = f"[{release_name(release)}]({release['url']}), {nice_date(release['date'])}"
        if not guide:
            get += ". Check the release notes for files and instructions for this model."
        else:
            get += f" · [{cell(guide['label'])}]({guide['url']})"
    elif row["kind"] in MOD_KINDS:
        get = "No release for this camera yet."
    elif guide:
        get = f"[{cell(guide['label'])}]({guide['url']})"
    else:
        get = f"[Project home]({row['url']})"
    return details + f"**Get it:** {get}\n{{ .card-get }}\n\n"


def project_card(catalogue, origin, row):
    text = '<div class="project-card" markdown="1">\n\n'
    if row.get("images"):
        picture = row["images"][0]
        text += f"![{cell(picture['alt'])}]({asset_link(origin, picture['path'])})\n{{ .card-image }}\n\n"
    text += f"[{cell(row['title'])}]({project_target(origin, row)}){{ .card-title }}\n\n"
    text += f"{row.get('tagline', row['summary'])}\n\n"
    names = [f["name"] for f in row.get("features", []) if f["status"] != "planned"][:3]
    if names:
        text += " · ".join(names) + "\n{ .card-features }\n\n"
    offered = [c for c in row["camera_ids"] if latest_release(row, c)
               or any(c in f["camera_ids"] for f in row.get("features", []))]
    names = [short_name(catalogue.records[c]["title"]) for c in offered or row["camera_ids"]]
    if names:
        text += "For: " + ", ".join(names) + "\n{ .card-cameras }\n\n"
    release = latest_release(row)
    meta = f"Latest: {release_name(release)}, {nice_date(release['date'])}" if release else label(row["kind"]).capitalize()
    text += meta + "\n{ .card-meta }\n\n"
    if release:
        text += release_notices(release, catalogue.records)
    return text + "</div>\n\n"


def camera_showcase(origin, camera, mods, records):
    camera_id = camera["id"]
    text = GENERATED + f"# {camera['title']} showcase\n\n"
    text += f"[Camera overview]({link(origin, view_path(camera))})\n\n"
    if not mods:
        return text + "The Atlas has no community firmware projects to showcase for this model yet.\n\n" + (
            f"[See research for this model]({link(origin, camera_research_path(camera))}).\n")
    text += risk_note(origin)
    for project in mods:
        title = cell(project["title"])
        text += f'\n<section class="model-panel" markdown="1">\n\n## {title} {{ #{slug(project["id"])} }}\n\n'
        text += for_camera(project, camera, include_feature_list=False)
        release = latest_release(project, camera_id)
        if release and release.get("warning"):
            text += release["warning"] + "\n{ .release-warning }\n\n"
        if not release_limit(release, camera_id):
            picture = next((image for image in project.get("images", [])
                            if image.get("camera_id") == camera_id
                            or ("camera_id" not in image and project["camera_ids"] == [camera_id])), None)
            if picture:
                text += f"![{cell(picture['alt'])}]({asset_link(origin, picture['path'])})\n{{ .hero-image }}\n\n"
                text += f"{picture['caption']} *{picture['credit']}.*\n{{ .image-caption }}\n\n"
            highlights = [f for f in project.get("features", [])
                          if camera_id in f["camera_ids"] and f["status"] in ("released", "beta", "alpha")]
            for feature in highlights[:3]:
                text += f"- **{cell(feature['name'])}** · {STATUS_LABELS[feature['status']]}. {feature['summary']}\n"
            if highlights:
                text += "\n"
        for request in testing_requests(project):
            if request["tester_camera_id"] == camera_id:
                text += f"[View the testing request]({request['url']})\n\n"
        links = [f"[Full project details]({project_target(origin, project, camera_id)})",
                 f"[Ask or report issues]({project['contribution_home']})"]
        if release and not release_limit(release, camera_id):
            links.append(report_link(camera, project, release["tag"]))
        text += " · ".join(links) + "\n\n</section>\n"
    return text


def camera_updates(catalogue, origin):
    text = '<section class="camera-updates" markdown="1">\n\n'
    requests = [(project, item) for project in catalogue.of_type("project") for item in testing_requests(project)]
    if requests:
        text += '<div class="tester-panel" markdown="1">\n\n## Projects looking for testers\n\n'
        for project, item in requests:
            camera = catalogue.records[item["tester_camera_id"]]
            target = project_target(origin, project, camera["id"])
            text += f"**[{cell(short_name(camera['title']))} · {cell(project['title'])}]({target})**\n\n"
            text += f"{item['summary']}. [View the testing request]({item['url']})\n\n"
        text += "</div>\n\n"
    releases = [(release, project) for project in catalogue.of_type("project") if (release := latest_release(project))]
    releases.sort(key=lambda pair: (pair[0]["date"], pair[1]["title"]), reverse=True)
    if releases:
        text += '## Recent releases\n\n<div class="release-list" markdown="1">\n\n'
        for release, project in releases[:6]:
            cameras = ", ".join(short_name(catalogue.records[c]["title"]) for c in release["camera_ids"])
            text += '<div class="release-item" markdown="1">\n\n'
            text += f"**{cell(cameras or 'Camera scope unspecified')}**\n{{ .release-model }}\n\n"
            text += release_line(origin, release, project) + "\n{ .release-head }\n\n"
            text += release_notices(release, catalogue.records)
            text += release["highlights"][0] + "\n\n</div>\n\n"
        text += "</div>\n\n"
    text += "</section>\n"
    return text


def people_markdown(catalogue, origin):
    """Maintainers and the projects they run, derived from project records."""
    people = {}
    for project in catalogue.of_type("project"):
        for person in project.get("maintainers", []):
            people.setdefault((person["label"], person["url"]), []).append(project)
    text = '<div class="people-grid" markdown="1">\n\n'
    for (name, url), projects in sorted(people.items(), key=lambda item: item[0][0].lower()):
        text += '<div class="person-card" markdown="1">\n\n'
        text += f"[{cell(name)}]({url}){{ .card-title }}\n\n"
        text += ", ".join(f"[{cell(p['title'])}]({link(origin, view_path(p))})" for p in projects) + "\n{ .card-meta }\n\n</div>\n\n"
    return text + "</div>\n"


def evidence_label(row):
    return f"{label(row['method'])}; {label(row['outcome'])}; {row['quality']} report; {label(row['identity_level'])}"


def observation_heading(row):
    method = {"physical-camera": "Camera test", "emulator": "Emulator test",
              "static": "Code inspection", "upstream-description": "Project description"}[row["method"]]
    outcome = {"reported-pass": "reported working", "pass": "passed", "reported-fail": "reported failure",
               "fail": "failed", "inconclusive": "inconclusive"}[row["outcome"]]
    return f"{method} · {outcome}"


def trait_title(catalogue, row):
    """Display name of a platform trait or native feature."""
    if row["category"] == "platform":
        return catalogue.taxonomy.get("traits", {}).get(row["trait"], {}).get("title", row["trait"])
    return catalogue.taxonomy["features"].get(row["feature_id"], {}).get("title", row["feature_id"])


def trait_value(row):
    if row["category"] == "platform":
        return row["value"]
    return PRESENCE[row["presence"]] + (f": {row['value']}" if row.get("value") else "")


def trait_rows(catalogue, category, firmware_ids):
    rows = [r for r in catalogue.of_type("reference") if r["category"] == category and r["firmware_ids"][0] in firmware_ids]
    order = list(catalogue.taxonomy.get("traits", {}) if category == "platform" else catalogue.taxonomy["features"])
    key = (lambda r: r["trait"]) if category == "platform" else (lambda r: r["feature_id"])
    return sorted(rows, key=lambda r: (order.index(key(r)) if key(r) in order else len(order), r["id"]))


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
            firmwares = [r for r in catalogue.of_type("firmware") if r["camera_id"] == row["id"]]
            if firmwares:
                facts.append("**Stock firmware covered:** " + ", ".join(dict.fromkeys(r["version"] for r in firmwares)))
            text += "\n" + " · ".join(facts) + "\n{ .facts }\n"
            projects = [records[p] for p in row["project_ids"]]
            mods = sorted((p for p in projects if installs(records, p, row["id"])),
                          key=lambda p: (release_limit(latest_release(p, row["id"]), row["id"]) is not None,
                                         latest_release(p, row["id"]) is None, p["title"]))
            showcase = camera_showcase_path(row)
            research = camera_research_path(row)
            outputs[showcase] = camera_showcase(showcase, row, mods, records)
            text += f"\n[View the showcase]({link(path, showcase)}){{ #features .btn .btn-primary }}\n"
            if mods:
                text += risk_note(path)
            text += "\n## Firmware projects { #projects }\n"
            text += glance(path, row, mods, records)
            text += f"\n[Read the evidence guide]({link(path, 'docs/evidence.md')}) · [Report a camera result]({link(path, 'docs/report.md')})\n"
            text += "\n## Developer resources { #research }\n\n"
            # Existing public camera links can still land on the relevant shortcut.
            text += '<span id="evidence"></span><span id="platform"></span><span id="firmware"></span><span id="talk"></span>\n\n'
            text += f"[Research for this model]({link(path, research)}) · [Community]({link(path, 'docs/community.md')})\n"
            overview, path = text, research
            text = GENERATED + f"# {row['title']} research\n\n{row['summary']}\n\n"
            text += f"[Camera overview]({link(path, view_path(row))}) · [Cross-body research]({link(path, 'docs/cross-body.md')})\n"
            text += research_actions(path, row)
            text += "\n## Projects and repositories\n\n"
            for project in projects:
                text += f"- [{cell(project['title'])}]({project_target(path, project, row['id'])}) · [Repository or project home]({project['url']})\n"
            if not projects:
                text += "No projects are catalogued for this model yet.\n"
            caps = [r for r in catalogue.of_type("capability") if r["camera_id"] == row["id"]]
            linked = {obs for cap in caps for key in ("evidence_refs", "contradicting_refs") for obs in cap[key]}
            other_observations = [ev for ev in catalogue.of_type("evidence")
                                  if ev["camera_id"] == row["id"] and ev["id"] not in linked]
            text += "\n## Claims and test evidence { #evidence }\n\n"
            if caps:
                text += '<div class="evidence-list" markdown="1">\n\n'
                for cap in caps:
                    text += '<div class="evidence-entry" markdown="1">\n\n'
                    observations = cap["evidence_refs"] + cap["contradicting_refs"]
                    for observation in observations:
                        ev = records[observation]
                        prefix = "Contradicting observation · " if observation in cap["contradicting_refs"] else ""
                        text += f"**{prefix}{observation_heading(ev)}** · {ref(path, observation)}\n\n"
                        text += f"{ev['quality']} report · {label(ev['identity_level'])}\n{{ .observation-meta }}\n\n"
                    if not observations:
                        text += "**No camera test recorded**\n\n"
                    project = records[cap["project_id"]]
                    target = project_target(path, project, row["id"])
                    text += f"Claim · {ref(path, cap['id'])}\n\n"
                    text += f"Project and build · [{cell(project['title'])}]({target}) / {cell(cap['mod_build'] or 'unspecified')}\n\n"
                    text += f"Availability · {label(cap['availability'])}\n\n</div>\n\n"
                text += "</div>\n\nResults belong to the named project and package. Emulator output does not establish physical-camera behaviour.\n"
            else:
                text += "No feature-level assertion is catalogued yet. This is a coverage gap, not a finding that modifications are impossible.\n"
            if other_observations:
                text += "\n### Other observations\n\n"
                text += "".join(f"- **{observation_heading(ev)}** · {ref(path, ev['id'])}\n" for ev in other_observations)
            venues = [r["id"] for r in catalogue.of_type("community") if set(r["project_ids"]) & set(row["project_ids"])]
            if venues:
                text += "\n## Where to talk { #talk }\n\n" + refs(path, venues) + ". For a reproducible bug, use the project's own issue tracker.\n"
            text += "\n## Firmware and technical reference { #platform }\n\n"
            text += refs(path, [r["id"] for r in firmwares]) + ".\n"
            for firmware in firmwares:
                platform = trait_rows(catalogue, "platform", [firmware["id"]])
                native = trait_rows(catalogue, "native-feature", [firmware["id"]])
                if platform or native:
                    text += f"\n### {cell(firmware['title'])}\n\n"
                    text += "What the stock firmware itself contains, separate from what projects add. Follow an entry for its sources.\n\n"
                    text += "| | Value | Status |\n|---|---|---|\n"
                    for r in platform + native:
                        text += f"| [{cell(trait_title(catalogue, r))}]({link(path, view_path(r))}) | {cell(trait_value(r))} | {REFERENCE_STATUS[reference_status(records, r)][0]} |\n"
            entries = [r for r in catalogue.of_type("reference")
                       if row["id"] in r["camera_ids"] and r["category"] not in TRAIT_CATEGORIES]
            if entries:
                text += "\n### Build-specific reference\n\n"
                text += "".join(f"- {ref(path, entry['id'])}\n" for entry in entries)
            outputs[path] = text + source_section(path, row)
            outputs[view_path(row)] = overview
            continue
        elif kind == "firmware":
            text += f"\n**Camera:** {ref(path, row['camera_id'])}. **Advertised version:** {row['version']}. **Internal build:** {label(row['internal_build'])}.\n"
            text += f"\n**Container SHA-256:** `{row['container_sha256']}`\n" if row["container_sha256"] else "\n**Container SHA-256:** not recorded in this entry.\n"
            text += f"\n{row['identity_note']}\n"
            entries = [r for r in catalogue.of_type("reference") if row["id"] in r["firmware_ids"]]
            for category, heading in (("platform", "Platform"), ("native-feature", "Built-in features")):
                rows = trait_rows(catalogue, category, [row["id"]])
                if rows:
                    text += f"\n## {heading}\n\n| | Value | Status |\n|---|---|---|\n"
                    text += "".join(f"| {ref(path, r['id'])} | {cell(trait_value(r))} | {REFERENCE_STATUS[reference_status(records, r)][0]} |\n" for r in rows)
            entries = [r for r in entries if r["category"] not in TRAIT_CATEGORIES]
            if entries:
                text += "\n## Technical reference\n\n" + "\n".join(f"- {ref(path, r['id'])}: {r['summary']}" for r in entries) + "\n"
        elif kind == "project":
            text = GENERATED + f"# {row['title']}\n\n{row.get('tagline', row['summary'])}\n\n"
            if any(installs(records, row, camera_id) for camera_id in row["camera_ids"]):
                text += risk_note(path) + "\n"
            text += project_actions(row, records) + research_actions(path, row)
            facts = [f"**Type:** {label(row['kind'])}"]
            if row["camera_ids"]:
                facts.append("**Camera details:** " + ", ".join(
                    f"[{cell(short_name(records[c]['title']))}](#for-{slug(c)})" for c in row["camera_ids"]))
            release = latest_release(row)
            if release:
                facts.append(f"**Latest release:** [{release_name(release)}]({release['url']}), {nice_date(release['date'])}")
            if row.get("maintainers"):
                facts.append("**Maintained by** " + ", ".join(f"[{cell(m['label'])}]({m['url']})" for m in row["maintainers"]))
            text += "\n" + " · ".join(facts) + "\n{ .facts }\n"
            if release:
                text += release_notices(release, records)
            cameras = list(row["camera_ids"])
            cameras.extend(c["id"] for c in catalogue.of_type("camera")
                           if row["id"] in c["project_ids"] and c["id"] not in cameras)
            if cameras:
                text += "\n## Cameras\n\n"
                requests = testing_requests(row)
                for camera_id in cameras:
                    camera = records[camera_id]
                    title = next((a for a in camera["aliases"] if a.startswith("Original ")), short_name(camera["title"]))
                    text += '<div class="model-panel" markdown="1">\n\n'
                    text += f"### {cell(title)} {{ #for-{slug(camera_id)} }}\n\n"
                    selected = latest_release(row, camera_id)
                    if selected and not release_limit(selected, camera_id) and installs(records, row, camera_id):
                        text += f"[Before you install: risks and recovery]({link(path, 'docs/before-you-install.md')})\n\n"
                    if camera_id in row["camera_ids"]:
                        text += for_camera(row, camera)
                    else:
                        text += "The camera page links this project as a research reference.\n\n"
                        claims = [cap["id"] for cap in catalogue.of_type("capability")
                                  if cap["camera_id"] == camera_id and cap["project_id"] == row["id"]]
                        if claims:
                            text += "Recorded findings: " + refs(path, claims) + ".\n\n"
                    for item in requests:
                        if item["tester_camera_id"] == camera_id:
                            text += f"[View the testing request]({item['url']}){{ .btn .btn-primary }}\n\n"
                    text += f"[Camera overview]({link(path, view_path(camera))}) · [Test results]({link(path, camera_research_path(camera))}#evidence)\n\n</div>\n\n"
            images = row.get("images", [])
            if images:
                picture = images[0]
                text += f"\n![{cell(picture['alt'])}]({asset_link(path, picture['path'])})\n{{ .hero-image }}\n\n{picture['caption']} *{picture['credit']}.*\n{{ .image-caption }}\n"
            text += "\n## About\n\n" + "\n\n".join(row.get("description", [row["status_summary"]])) + "\n"
            if row.get("goals"):
                text += "\n### What it's working towards\n\n" + "\n".join(f"- {g}" for g in row["goals"]) + "\n"
            if row.get("features"):
                text += "\n## Features\n\nAs the project describes them. Status is the project's own; linked evidence is the Atlas's record of what was reported or observed.\n\n"
                text += '<div class="feature-grid" markdown="1">\n\n'
                for feature in row["features"]:
                    text += '<div class="feature-card" markdown="1">\n\n'
                    text += f"**{cell(feature['name'])}** {pill(feature['status'])}\n{{ .feature-head }}\n\n{feature['summary']}\n\n"
                    meta = []
                    if feature["camera_ids"]:
                        meta.append(", ".join(f"[{cell(short_name(records[c]['title']))}]({link(path, view_path(records[c]))})" for c in feature["camera_ids"]))
                    if feature.get("since"):
                        meta.append(f"since {feature['since']}")
                    if feature.get("capability_id"):
                        meta.append(f"[Evidence]({link(path, view_path(records[feature['capability_id']]))})")
                    if meta:
                        text += " · ".join(meta) + "\n{ .card-meta }\n\n"
                    text += "</div>\n\n"
                text += "</div>\n"
            if len(images) > 1:
                text += "\n## Gallery\n\n" + '<div class="gallery" markdown="1">\n\n'
                for picture in images[1:]:
                    text += f'<div class="gallery-item" markdown="1">\n\n![{cell(picture["alt"])}]({asset_link(path, picture["path"])})\n\n{picture["caption"]} *{picture["credit"]}.*\n{{ .image-caption }}\n\n</div>\n\n'
                text += "</div>\n"
            if row.get("releases"):
                text += "\n## Releases\n\n"
                for release in row["releases"]:
                    text += '<div class="release-item" markdown="1">\n\n'
                    text += f"**[{cell(release['title'])}]({release['url']})**" + (' <span class="pill pill-alpha">Pre-release</span>' if release["prerelease"] else "") + f" · {nice_date(release['date'])}\n{{ .release-head }}\n\n"
                    text += "\n".join(f"- {h}" for h in release["highlights"]) + "\n\n"
                    text += release_notices(release, records)
                    for camera_id in release["camera_ids"]:
                        camera = records[camera_id]
                        text += f"{cell(short_name(camera['title']))} · {report_link(camera, row, release['tag'])}\n\n"
                    if release.get("warning"):
                        text += f"{release['warning']}\n{{ .release-warning }}\n\n"
                    text += "</div>\n\n"
            communities = [r["id"] for r in catalogue.of_type("community") if row["id"] in r["project_ids"]]
            if communities:
                text += "\n## Where to talk\n\n" + refs(path, communities) + ". For a reproducible bug, use the project's issue tracker.\n"
            if any(installs(records, row, camera_id) for camera_id in row["camera_ids"]):
                text += (f"\n[Report a camera result]({link(path, 'docs/report.md')}) with the exact model, "
                         "starting firmware, build, file hash if known, steps and outcome.\n")
            text += "\n## Related work\n\n" + refs(path, row["related_projects"]) + ". These links do not assign ownership or imply identical implementations.\n"
            text += f"\n## Research notes\n\n{row['status_summary']}\n"
            if row.get("work_items"):
                text += "\n" + "".join(f"- [{item['summary']}]({item['url']}) — {label(item['state'])}; owner: {item.get('owner') or 'not assigned here'}.\n" for item in row["work_items"])
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
            if row["camera_id"]:
                text += "\n" + report_link(records[row["camera_id"]], records[row["project_id"]], row["mod_build"]) + "\n"
            text += f"\n[Share a research finding]({link(path, 'docs/research-with-ai.md')}#share-what-you-find)\n"
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
        elif kind == "reference":
            status, tone = REFERENCE_STATUS[reference_status(records, row)]
            facts = [f"**Category:** {label(row['category'])}", f'<span class="pill pill-{tone}">{status}</span>']
            if row.get("address"):
                address = row["address"]
                span = f"`{address['value']}`" + (f" to `{address['end']}`" if address.get("end") else "")
                facts.insert(1, f"**Address:** {span} ({label(address['space'])})")
            if row["category"] in TRAIT_CATEGORIES:
                facts.insert(1, f"**{cell(trait_title(catalogue, row))}:** {cell(trait_value(row))}")
            text += "\n" + " · ".join(facts) + "\n{ .facts }\n"
            text += f"\n**Build:** {refs(path, row['firmware_ids'])} · **Cameras:** {refs(path, row['camera_ids'])}\n"
            text += f"\n{row['note']}\n"
            if row.get("consequence"):
                text += f"\n> **What happens:** {row['consequence']}\n"
            text += "\n## Observations\n\n"
            for item in row["observations"]:
                who = f" ({ref(path, item['project_id'])})" if item.get("project_id") else ""
                text += f"- **{label(item['method']).capitalize()}**{who}: {item['summary']} Source: {ref(path, item['source_ref'])}.\n"
            if row["conflicts"]:
                text += "\n## Conflicting reports\n\n" + "".join(f"- {c['summary']} Source: {ref(path, c['source_ref'])}.\n" for c in row["conflicts"])
            text += f"\n**[Full detail upstream]({row['upstream_detail']})**\n"
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
            text += f"[Browse cameras by TruePic generation]({link(path, 'docs/truepic-generations.md')}).\n\n"
            text += camera_finder(catalogue, path)
            for line in CAMERA_LINES:
                members = sorted((r for r in rows if camera_line(r["title"]) == line), key=lambda r: r["title"])
                if not members:
                    continue
                text += f"## {line}\n\n" + '<div class="camera-grid" markdown="1">\n\n'
                for row in members:
                    projects = [records[p] for p in row["project_ids"]]
                    mods = [p for p in projects if installs(records, p, row["id"])]
                    releases = [r for p in mods if (r := latest_release(p, row["id"]))]
                    released = len(releases)
                    meta = [plural(len(mods), "mod or port", "mods or ports") + (f", {released} with a release" if released else ", none released yet") if mods else "No mods catalogued"]
                    for release in releases:
                        limit = release_limit(release, row["id"])
                        if limit:
                            meta.append(f"{release_name(release)}: {limit}")
                    if row["coverage"] == "discovery-only":
                        meta.append("discovery only")
                    text += '<div class="camera-card" markdown="1">\n\n'
                    text += f"[{cell(short_name(row['title']))}]({link(path, view_path(row))}){{ .card-title }}\n\n"
                    text += f"{', '.join(row['model_codes'])}\n{{ .model-code }}\n\n{row['summary']}\n\n"
                    text += " · ".join(meta) + "\n{ .card-meta }\n\n</div>\n\n"
                text += "</div>\n\n"
            outputs[path] = text + camera_updates(catalogue, path)
            continue
        if kind == "reference":
            rows = catalogue.of_type("reference")
            hazards = [r for r in rows if r["category"] == "hazard"]
            if hazards:
                text += "## Trouble spots\n\n| Rule | Cameras | Status |\n|---|---|---|\n"
                for row in hazards:
                    text += f"| {ref(path, row['id'])} | {', '.join(short_name(records[c]['title']) for c in row['camera_ids'])} | {REFERENCE_STATUS[reference_status(records, row)][0]} |\n"
                text += "\n"
            for category, heading, intro in (
                    ("native-feature", "Built-in features by build", "What each stock firmware contains, before any project changes it. Absent means checked and not found; a blank cell means nobody has recorded it."),
                    ("platform", "Platform by build", "Hardware and layout facts per stock firmware build.")):
                cat_rows = [r for r in rows if r["category"] == category]
                builds = [f for f in catalogue.of_type("firmware") if any(r["firmware_ids"][0] == f["id"] for r in cat_rows)]
                if not builds:
                    continue
                keys = list(dict.fromkeys(r.get("trait") or r["feature_id"] for r in trait_rows(catalogue, category, [f["id"] for f in builds])))
                text += f"## {heading}\n\n{intro}\n\n| | " + " | ".join(cell(f"{short_name(records[f['camera_id']]['title'])} {f['version']}") for f in builds) + " |\n"
                text += "|---|" + "---|" * len(builds) + "\n"
                for key in keys:
                    cells = []
                    for firmware in builds:
                        match = [r for r in cat_rows if (r.get("trait") or r["feature_id"]) == key and r["firmware_ids"][0] == firmware["id"]]
                        cells.append(f"[{cell(trait_value(match[0]))}]({link(path, view_path(match[0]))})" if match else "")
                    title = trait_title(catalogue, {"category": category, "trait": key, "feature_id": key})
                    text += f"| {cell(title)} | " + " | ".join(cells) + " |\n"
                text += "\n"
            for firmware in catalogue.of_type("firmware"):
                entries = sorted((r for r in rows if r.get("address") and r["firmware_ids"] == [firmware["id"]]), key=lambda r: (r["address"]["space"], int(r["address"]["value"], 16)))
                if entries:
                    text += f"## {records[firmware['camera_id']]['title']}, {firmware['title']}\n\n| Name | Address | Category | Status |\n|---|---|---|---|\n"
                    for row in entries:
                        text += f"| {ref(path, row['id'])} | `{row['address']['value']}` | {label(row['category'])} | {REFERENCE_STATUS[reference_status(records, row)][0]} |\n"
                    text += "\n"
            text += "What belongs here, and what stays upstream: [the reference policy](../../maintenance/reference-policy.md). For detailed research, start with [Olympus firmware research](../projects/oly-fw-analysis.md).\n"
            outputs[path] = text
            continue
        if kind == "project":
            for title, kinds in PROJECT_GROUPS:
                members = [r for r in catalogue.of_type("project") if r["kind"] in kinds]
                members.sort(key=lambda r: (bool(r.get("images")), (latest_release(r) or {}).get("date", ""), r["title"]), reverse=True)
                if members:
                    text += f"## {title}\n\n" + '<div class="project-grid" markdown="1">\n\n'
                    text += "".join(project_card(catalogue, path, r) for r in members) + "</div>\n\n"
            outputs[path] = text
            continue
        text += "| Entry | What you will find | Visit |\n|---|---|---|\n" if kind == "community" else "| Entry | What you will find |\n|---|---|\n"
        for row in catalogue.of_type(kind):
            visit = f" [{label(row['platform']).title()}]({row['url']}) |" if kind == "community" else ""
            text += f"| {ref(path, row['id'])} | {cell(row['summary'])} |{visit}\n"
        if kind == "community":
            text += "\n[How to turn a discussion into durable knowledge](../../docs/add.md#from-a-discussion-to-documentation).\n"
        outputs[path] = text

    path = "views/research/index.md"
    text = GENERATED + "# Research by camera\n\nChoose a model for its firmware builds, projects, technical reference and test results.\n"
    for line in CAMERA_LINES:
        members = sorted((r for r in catalogue.of_type("camera") if camera_line(r["title"]) == line),
                         key=lambda r: r["title"])
        if members:
            text += f"\n## {line}\n\n"
            for camera in members:
                codes = ", ".join(camera["model_codes"])
                text += f"- [{cell(short_name(camera['title']))}]({link(path, camera_research_path(camera))})"
                text += f" · {codes}\n" if codes else "\n"
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
        if any(camera["id"] in r["camera_ids"] for r in catalogue.of_type("reference")):
            text += f"\nCompact technical reference for this camera: [reference shard](../reference/{slug(camera['id'])}.md).\n"
        text += "\nThen choose the [task topic](../topics/index.md). Read exact upstream sections only as needed. Do not transfer test results between models or packages.\n"
        outputs[path] = text

    for camera in catalogue.of_type("camera"):
        entries = [r for r in catalogue.of_type("reference") if camera["id"] in r["camera_ids"]]
        if not entries:
            continue
        path = f"agents/routes/reference/{slug(camera['id'])}.md"
        text = GENERATED + f"# Technical reference: {camera['title']}\n\n"
        text += "Exact-build facts only: never apply an address to another build or body. Status: camera-confirmed > corroborated > single source; disputed entries list their conflict. Follow Detail for the explanation.\n\n"
        details = []

        def detail(url):
            if url not in details:
                details.append(url)
            return f"[d{details.index(url) + 1}]"

        hazards = [r for r in entries if r["category"] == "hazard"]
        if hazards:
            text += "## Trouble spots\n\n| Rule | Status | Detail |\n|---|---|---|\n"
            text += "".join(f"| {cell(r['title'])} | {reference_status(records, r)} | {detail(r['upstream_detail'])} |\n" for r in hazards) + "\n"
        for firmware in catalogue.of_type("firmware"):
            traits = trait_rows(catalogue, "platform", [firmware["id"]]) + trait_rows(catalogue, "native-feature", [firmware["id"]])
            traits = [r for r in traits if r in entries]
            if traits:
                text += f"## {firmware['id']}: platform and built-in features\n\n| Fact | Value | Status | Detail |\n|---|---|---|---|\n"
                text += "".join(f"| {cell(trait_title(catalogue, r))} | {cell(trait_value(r))} | {reference_status(records, r)} | {detail(r['upstream_detail'])} |\n" for r in traits) + "\n"
            rows = sorted((r for r in entries if r.get("address") and r["firmware_ids"] == [firmware["id"]]), key=lambda r: int(r["address"]["value"], 16))
            if rows:
                text += f"## {firmware['id']}\n\n| Name | Space | Address | Kind | Status | Detail |\n|---|---|---|---|---|---|\n"
                for r in rows:
                    span = r["address"]["value"] + (f"..{r['address']['end']}" if r["address"].get("end") else "")
                    text += f"| {cell(r['title'])} | {r['address']['space']} | `{span}` | {r['category']} | {reference_status(records, r)} | {detail(r['upstream_detail'])} |\n"
                text += "\n"
        text += "".join(f"[d{i + 1}]: {url}\n" for i, url in enumerate(details)) + "\n"
        text += f"Records: {', '.join(sorted({f'[{Path(catalogue.paths[r["id"]]).name}]({link(path, catalogue.paths[r["id"]])})' for r in entries}))}.\n"
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
