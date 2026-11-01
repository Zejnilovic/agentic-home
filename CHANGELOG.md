# Changelog

What changed in agentic-home. The next version's changes are collected here; each released version's notes, including manual steps, are on its GitHub release, linked below. To see what an update would change, run `agd --home status`.

Version numbers: **major** when something is renamed or removed and existing installs need manual changes, **minor** for new skills, agents or rules, **patch** for wording and fixes.

A bullet can end with the issues it touches: `(#12)` means this release fixes #12, `(ref #20)` means a related change that leaves #20 open, and they combine as `(ref #20, ref #11, #12)`. When the release is out, each issue gets a comment, and the fixed ones are closed.

## 0.1.1 (unreleased)

- `kit-authoring`: a home kit needs plain ASCII names, and agd refuses every `.claude/settings*` file, not only `settings.json`.

## Released

- [0.1.0](https://github.com/Zejnilovic/agentic-home/releases/tag/v0.1.0) (2026-11-01)
