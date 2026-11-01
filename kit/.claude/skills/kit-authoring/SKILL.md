---
name: kit-authoring
description: Create or change a kit source, the git repository holding a kit that agd installs into projects or a person's home folder - decide what the kit is for, split it into packs, write its instructions, agents and skills, check it with agd check, try it and release it. Use when asked to create, split, review or release a kit, or to turn a project's agentic setup into something others can install.
---

<!-- From agentic-home. Kit updates replace this file except a "## This project" section at the end, which belongs to the project. Edit nothing else. -->

# Kit authoring

A **kit** is what agd installs in a project: instructions, agents, skills and hooks. A **kit source** is the git repository that holds a kit, with its `packs.txt` and release tags. The format is in the [reference](https://zejnilovic.github.io/agd/sources/) and `agd check` enforces it, so spend your attention on what the kit says.

Commit, tag and push only when the user asks.

## 1. Find out what the kit is for

Read what already exists first: an existing setup in the repository is the best starting point. Then ask only what you can't find out:

- Who installs it, and what should change in how their agents work?
- Is it for projects, or for a person's home folder, where it reaches every project on their machine? A home kit has rules of its own: see "A kit for the home folder".
- Does it stand alone, or go on top of another source such as agentic-defaults?
- Is it public, or does it stay inside a company?

Write the purpose in one sentence. If the rules fit only one project, it doesn't need a kit: they belong in that project's `AGENTS.md`.

## 2. Choose the layout

- **A new repository, or one that doesn't use the setup itself:** files in `kit/`, mirroring a project's root. `kit/.claude/agents/reviewer.md` lands as `.claude/agents/reviewer.md`.
- **A repository that uses its setup at its own root:** `root .` in `packs.txt`. Only files listed in a pack install.

agd names the source after its repository, so keep that name distinctive. Paths can't contain spaces or quotes.

## 3. Split it into packs

Start with one pack. Add another only when some projects want a part that others don't, such as one framework.

```text
min-agd 0.4.0

pack core
  AGENTS.md
  .claude/agents/reviewer.md
  .claude/skills/api-review/

pack flask requires core
  .claude/skills/flask/
```

- Keep a skill's folder in one pack, and end the folder's path with `/`.
- When a file names an agent or skill in another pack, its pack `requires` that pack. Another source's pack is `<source>:<pack>`.
- Set `min-agd` when the kit needs a feature of a newer agd.
- Avoid paths another source you expect beside this one also ships, such as `AGENTS.md` on top of agentic-defaults: the project has to choose one of the two.

## 4. Write the files

Put each thing where it costs least:

| What | Where | Why |
|---|---|---|
| Rules for all work | `AGENTS.md` | Read every session, so keep it short |
| A procedure needed sometimes | A skill | Read only when its description matches |
| A role that needs its own context or model | An agent | Runs apart from the main conversation |

- Write each `description` to say what it does and when to use it. It decides when the file gets read.
- Keep only rules that change what an agent does. Leave out what agents do anyway and what the code already shows.
- Leave out facts about any one project: stack, commands, names. A project adds those itself.
- Never include secrets, and in a public kit no internal names or URLs.
- agd only copies files and never runs them. A script you ship runs only when an agent or a person runs it, so say when.

Three parts of a kit file belong to the project, and updates keep them:

- **`model:`** Set it as your default. Projects may change it.
- **`tools:`** Leave it out.
- **`## This project`**, and everything under it to the end of the file. Leave it out, except where a project should fill in a section, such as the end of a root `AGENTS.md`.

Start each file with a short comment that names the source and says which parts the project may change, so agents put a project's changes in the right place. The comment at the top of this file is an example.

### A kit for the home folder

People install it with `agd --home init <source>`, and it applies to every project on their machine, so it holds only what they'd want everywhere.

- **Only files under `.claude/`.** agd stops on anything else, including a root `CLAUDE.md` or `AGENTS.md`, which would load in every project under the home folder.
- **Rules go in `.claude/rules/<name>.md`.** Most people already have a `~/.claude/CLAUDE.md`, and agd leaves it alone, so a kit's copy wouldn't install.
- **No `.claude/settings.json`.** agd stops on that too, since its hooks would run in every project. Tell people what to add to their own settings instead.
- **Distinctive skill names.** A personal skill beats a project's skill with the same name, in every project.

## 5. Check it

Run this in the kit source, and fix every error and warning:

```bash
agd check
```

It reads the working tree, so it needs no commit. A source with no release tag yet is an error until the first tag; that one can wait for step 7.

## 6. Try it in a scratch project

agd installs committed files, so this step needs a commit and a tag. Ask first if the user hasn't said to make them.

```bash
agd init <path to the kit source>
```

```bash
agd status
```

For a home kit, use a scratch home folder, so the person's own stays untouched:

```bash
HOME=<scratch folder> agd --home init <path to the kit source>
```

Read what landed. To see what the next release does to an installed copy, commit a change in the source, then run this in the scratch project:

```bash
agd update --to <sha>
```

## 7. Release it

- Tag releases `v<major.minor.patch>`. Never move a tag: projects that installed it stop until they accept the change.
- Write release notes, with any manual steps a project needs. agd links them from `agd status` for sources on GitHub.
- Treat a renamed or removed file or pack as a breaking change, and say what a project should do. agd deletes a removed file only when the project hasn't changed it.

Report what the kit does, its packs, the `agd check` result, what you tried, and the install command: `agd init <owner>/<repository>` for projects, `agd --home init <owner>/<repository>` for a home kit.
