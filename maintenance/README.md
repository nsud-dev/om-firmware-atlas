# Maintain the Atlas

The scripts maintain documentation only. Python 3.10+ and `requirements.txt` are the complete application dependencies. Use an isolated environment. No vendor firmware, camera access or upstream development toolchain is needed.

Before committing or pushing, follow [the identity gate](git-identity.md). Authentication, author and committer are checked separately; an inherited machine identity must never be used.

## Commands

```sh
python scripts/atlas.py generate
python scripts/atlas.py check
python -m unittest discover -s tests -v
python scripts/atlas.py build
python scripts/atlas.py route --job research --camera om5-ii --topic emulation
python scripts/atlas.py freshness --fetch
```

`check` validates schemas, identity/reference semantics, dependencies, local links, generated drift and fixed routing cases. `build` validates and builds MkDocs strictly from an ignored staging tree. `generate` writes only Atlas-owned `views/` and `agents/routes/`; do not edit those files manually. Costs are UTF-8 bytes and `ceil(bytes / 4)` approximate tokens, not measured model usage.

Read [record format](record-format.md) for canonical data and [the implementation plan](plan.md) for scope and remaining improvements. [Decisions](decisions/0001-foundation.md) record why the library is built this way.

## Publication and review

PR checks use read-only repository access. The main workflow validates, tests, builds and publishes GitHub Pages using the `github-pages` environment. The site displays its source commit and publication time. Only `main` and manual runs on `main` can publish. Scheduled freshness checks create a report artifact and rebuild the main site so age notices advance; they never change factual records.

The initial setup was explicitly authorised to push to main. Now, changes reach `main` through PRs, and the **Atlas validation** check must pass. Another person's approval is not required: the owner can review and merge their own PRs. Agents raise PRs and never approve or merge. CODEOWNERS names the owner for schemas, policies, scripts and workflows. Shared credentials cannot prove that an action was performed by a human. Branch protection is a repository setting, not something AGENTS.md can enforce. [How the Atlas works](../docs/how-it-works.md) explains this for contributors.

## Scope of verification

Routing cases verify deterministic selection, order, excluded bulk reads and estimated cost. They do not prove that every external coding agent obeys the instructions. Perform representative client smoke checks when changing the entry contract. Site builds validate links/structure, not the truth of free prose. Inspect rendered pages when changing content/layout and attach preview evidence to a PR.

Freshness reports distinguish unchanged, changed, unavailable and unsupported comparison. They do not mutate review dates. Keep reports in CI artifacts or `.build/`, not as edited historical logs. Substantive changes still need an agent/human review and a PR.
