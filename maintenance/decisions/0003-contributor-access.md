# 0003 — Use normal GitHub contributor permissions

Status: accepted, 17 November 2026.

This is a shared documentation repository. A maintainer's personal choice of GitHub account and commit email must not become an identity requirement for every contributor.

Remove the custom author/committer allowlist, credential checks, Git hooks and CI history audit. Normal GitHub permissions control access. Atlas validation continues to check documentation schemas, references, evidence scope, generated output, routing regressions and the site build.

The first external PR exposed a second problem with auditing every checked-out commit: GitHub Actions checked a temporary test merge whose generated author email differed from the submitted commit. The submitted commit used the expected account and no-reply identity. This metadata restriction was unrelated to documentation quality.

Main still requires PRs and successful validation. Maintainers review and merge, including their own PRs; a separate approving review is not mandatory. Contributor identity preferences remain each contributor's responsibility.
