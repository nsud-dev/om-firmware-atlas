# Use the Atlas with your AI

Open your coding agent in your firmware project. Give it the Atlas repository link and your question. The repository includes instructions for finding relevant camera tests, earlier attempts and known pitfalls. If your agent works offline, give it a local copy instead.

## Start an investigation

```text
Use https://github.com/xulfr/om-firmware-atlas to help me investigate [question] on [camera and firmware].
```

For example, you might ask whether an OM-3 look exporter can write files for an OM-5 Mark II. Both projects use the filename `LOOKS.BIN`, but the cameras expect different formats. The Atlas links to both descriptions so you can check which fields your exporter needs to write. [Comparison and original sources](../knowledge/interfaces/looks.md).

## Share what you find

Keep the detailed work in your project. Give your agent a public source for your finding, including failed or partial results.

```text
Update https://github.com/xulfr/om-firmware-atlas with my findings from [commit, release or report URL].
```

The repository instructions guide the agent through preparing a pull request for review. You can also [submit a source or correction](https://github.com/xulfr/om-firmware-atlas/issues/new?template=source.yml) or [report a camera result](report.md).
