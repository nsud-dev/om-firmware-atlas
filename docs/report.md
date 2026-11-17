# Report a camera result

A report from a real camera is the most valuable thing you can add, whether it worked, failed or was only partly checked. A partial report is still useful, as long as it is honest about what is missing.

[Open a camera report](https://github.com/xulfr/om-firmware-atlas/issues/new?template=camera-report.yml){ .btn .btn-primary }

You can also post in the project's own issue tracker; a contributor can then cite that post as a source.

## What to include

- **Camera:** the exact model and generation, for example OM-5 Mark II rather than OM-5.
- **Stock firmware:** the version you started from.
- **Modification:** the project, and the exact build or version.
- **Package identity:** the file's SHA-256 hash, if you recorded it. Write "unknown" if not; a hash published by the project is not the same as one you checked yourself.
- **Test date:** when you tested, or "unknown". The date you post is recorded separately.
- **What you did and what happened:** include failures, odd behaviour and anything you did not check.
- **Recovery:** if something went wrong and you restored the camera, describe the state and what you did. One recovery doesn't prove every failure is recoverable.

Leave out serial numbers and other personal details.

## What happens next

A contributor turns your report into an observation record linked to that exact camera, firmware and build. It appears on the camera page with its gaps shown. Your report is never applied to another model or package. [Reading the evidence](evidence.md) explains how reports are labelled.
