# Working agreement

agentic-home is a kit source: a kit for a person's home folder, installed and updated by [agd](https://github.com/Zejnilovic/agd) with `agd --home init`. It reaches every project on their machine, so it holds only what they'd want everywhere.

## The kit

- Files in `kit/` land in `~`. agd installs only under `.claude/`, with plain ASCII names and never a `.claude/settings*` file, so anything else in a pack stops the install. Check with `agd check`, once a tag exists.
- Keep each skill's folder in one pack in `packs.txt`, and give skills distinctive names: a personal skill beats a project's skill with the same name.
- No `CLAUDE.md` in the kit: most people have their own, and its text would load in every session. Rules go in `.claude/rules/<name>.md`.

## Commands

- Test: `python3 -m unittest discover -s tests`
- Start a version: `bash scripts/bump.sh <version>`, then replace the TODO in `CHANGELOG.md`.

## Releases

- Every change to `kit/` or `packs.txt` belongs to a version, and tags never move.
- Name the issues a bullet touches in a marker at its very end: `(#12)` means the release fixes #12 and closes it, `(ref #20)` means a related change that leaves #20 open, and they combine as `(ref #20, ref #11, #12)`. A test fails on any other form in the unreleased entry, and on a closing word before an issue number, because GitHub would act on those words if they reached a commit message. Commit messages use `Refs #12`.
- To release: push everything to `main`, then run the **Release** workflow (`gh workflow run release.yml`), first with `-f dry_run=true`. Don't tag by hand. It runs the tests, moves the entry into the GitHub release, checks the issues the notes name before pushing, tags `v<version>`, runs `agd check`, and closes or comments on those issues last. `scripts/close_issues.py` is the same script as in agd and agentic-defaults, apart from its `HOW_TO_GET_IT` line.
