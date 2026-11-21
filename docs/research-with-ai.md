# Use the Atlas with your AI

Open Claude Code in your own firmware project. Give it the Atlas repository link, your exact camera and firmware, and the question you're trying to answer. The Atlas points your agent to earlier attempts, known pitfalls and the original sources. You can use it with any coding agent that can read the repository.

## Start an investigation

Paste this into your session and replace the two bracketed fields. If your agent works offline, give it a local checkout of the Atlas in place of the URL.

```text
Use https://github.com/xulfr/om-firmware-atlas to help me investigate [question] on [exact camera and firmware].
Start with AGENTS.md and agents/start.md. Follow the research route for my camera and topic.
Before changing code, tell me what others have already tried, what failed, and which pitfalls apply to my build.
Link the original sources. Distinguish camera tests, emulator results and findings from reading code.
What is still unknown? Suggest the next check in my project and explain what it would tell us.
```

**For example, “Can my OM-3 look exporter also write files for an OM-5 Mark II?”** Both projects use the filename `LOOKS.BIN`. The Atlas points to different file formats: OM3P on the OM-3 and OM5F on the Mark II. The field counts, names and validation differ. With those sources in hand, ask your agent to compare the fields your exporter writes with those the Mark II reader accepts. That gives you a concrete compatibility check before you spend time trying the file on a camera. [Comparison and original format references](../knowledge/interfaces/looks.md).

For a different question, the [research index](research.md) covers common failure modes and hardware families. The [technical reference](../views/reference/index.md) links build-specific findings to the evidence behind them.

**For future sessions**, you can put this line in your own project’s `CLAUDE.md` so you don't have to remember the prompt each time:

```text
Before a new firmware investigation, consult https://github.com/xulfr/om-firmware-atlas for this camera, firmware and topic. Bring forward relevant sources, failed attempts and open questions.
```

## Share what you find

Keep the detailed work in your project. Once you have a public commit, release or test report, give your agent that link as well as the Atlas link. A failed test is worth sharing too: say which build you tried, what you expected and what actually happened.

```text
Update https://github.com/xulfr/om-firmware-atlas with my work from [public commit, release or report URL].
Follow the Atlas AGENTS.md and agents/start.md. Compare my source with the existing records.
Add the new finding for the exact camera, firmware and project build. Record how it was tested, any failure or conflicting result, and what remains untested.
Link back to the detailed work. Regenerate, check, test and build, then open a focused Atlas pull request for human review. Do not approve or merge it.
```

You can also [submit a source or correction](https://github.com/xulfr/om-firmware-atlas/issues/new?template=source.yml) or [report a camera result](report.md). Include the file hash if you checked it. A reviewed finding then becomes part of the starting point for the next researcher.
