# product-planning

A Claude Code plugin that takes a product idea through a planning workflow you can reuse in any project:

```
brainstorm/research → Now/Next/Later roadmap → prioritized epics → user stories (Given/When/Then) → GitHub Issues / Jira
```

The skills are generic. Everything specific to a project (product, personas, constraints, prioritization framework, file paths, tracker) lives in that project's **`product/workflow.yaml`**.

| Skill | Status | What it does |
|---|---|---|
| `/product-planning:init` | ✅ | Interviews you, writes `product/workflow.yaml`, and validates it |
| `/product-planning:brainstorm` | 🚧 stub | Research notes → `paths.research` |
| `/product-planning:roadmap` | 🚧 stub | Now/Next/Later roadmap → `paths.roadmap` |
| `/product-planning:backlog` | 🚧 stub | One file per epic → `paths.backlog` |
| `/product-planning:stories` | 🚧 stub | One file per story, with acceptance criteria → `paths.stories` |
| `/product-planning:sync` | ✅ | One-way sync of **approved** epics and stories → tracker |

## Requirements
- Claude Code with plugin support
- `python3` with **PyYAML** (`python3 -m pip install --user pyyaml`). If the `jsonschema` package is installed it's used for validation. Otherwise a built-in validator is used.
- For sync, one of these MCP servers (see [Tracker setup](#tracker-setup))

## Install

In Claude Code:
```
/plugin marketplace add <owner>/<repo>          # the GitHub repo that holds this plugin
/plugin install product-planning@product-planning-marketplace
```
Or from a shell: `claude plugin marketplace add <owner>/<repo>` followed by `claude plugin install product-planning@product-planning-marketplace`.

For local development, run `claude --plugin-dir /path/to/this/repo`, or `/plugin marketplace add /path/to/this/repo`.

## Update
```
/plugin marketplace update product-planning-marketplace
```
Then reinstall or update the plugin from `/plugin`. Installed copies are pinned to the `version` in `.claude-plugin/plugin.json`, so **bump `version` whenever you publish changes**.

## Start a new project
1. Open Claude Code in the project and run `/product-planning:init`. It asks about the product, personas, constraints, prioritization, estimation and tracker, then writes and validates `product/workflow.yaml`. An annotated example of every field is in [`workflow.example.yaml`](workflow.example.yaml). The schema is [`schemas/workflow.schema.json`](schemas/workflow.schema.json).
2. Set up the tracker's MCP server with the command `init` prints.
3. Work through the stages in order (see below).
4. Run `/product-planning:sync --dry-run` to preview, then `/product-planning:sync` to push.

You can validate the config at any time with:
`python3 <plugin>/scripts/pp.py validate product/workflow.yaml`

## How the stages connect

```
workflow.yaml ──┬─────────────┬──────────────┬──────────────┬─────────────┐
                ▼             ▼              ▼              ▼             ▼
           brainstorm ──▶ roadmap ──▶     backlog   ──▶   stories  ──▶   sync
        paths.research  paths.roadmap  paths.backlog   paths.stories  tracker.*
         (notes .md)    (Now/Next/     (EPIC-NNN-*.md) (US-NNN-*.md)  GitHub/Jira
                         Later)                                       one-way
```

- Each stage reads the previous stage's output from the configured `paths`, and stops and asks you when an input is missing.
- Epics and stories share one frontmatter contract, described in [`schemas/item-frontmatter.md`](schemas/item-frontmatter.md):
  ```yaml
  id: US-001
  title: Reset password by email
  epic: EPIC-001
  status: draft        # draft | review | approved
  priority: 42
  estimate: 3
  tracker_id: null     # written by sync
  tracker_url: null    # written by sync
  ```
- **Only `status: approved` items are synced.** Moving an item from draft to review to approved is your review gate.
- Templates are in [`templates/`](templates/). To use your own, set `templates.epic`, `templates.story` or `templates.roadmap` in `workflow.yaml`.

## Sync behaviour
- Validates `workflow.yaml`. It stops if the file is invalid or if `tracker.type: none`.
- Checks that the MCP server is available. If it isn't, it prints the exact `claude mcp add` command and stops.
- Always shows a **dry-run table** of create, update, skip and error first, and only continues after you reply **yes**. `--dry-run` stops after the table.
- **Idempotent.** After creating an issue it writes `tracker_id` and `tracker_url` into the file. Next time the item is **updated**, not duplicated.
- **Epic links.** GitHub uses a sub-issue, with a fallback of an `epic:<ID>` label plus a "Parent epic: #N" line. Jira uses `parent` or the Epic Link field.
- **Acceptance criteria.** On GitHub they go into the issue body as a Given/When/Then checklist. On Jira they go into the description or the configured custom field.
- **Archive (optional).** After a successful real sync it offers to move the synced story files to `paths.archive` (default `product/archive/`) and add that folder to `.gitignore`. Archived files stay only on your machine. `plan` still reads the archive so an archived id is never re-created.
- Ends with a summary of what was created, updated, skipped and failed, with reasons.

> **One-way only: files → tracker.** Sync never pulls tracker changes back. Edits made in GitHub or Jira to the title, body or synced fields are **overwritten** on the next sync. Status, assignee and sprint are never touched. Keep the files as the source of truth.

## Tracker setup
No secrets go into `workflow.yaml`, and the validator rejects anything that looks like a token or credential. Authentication is handled by the MCP server:

- **GitHub** (remote GitHub MCP server, PAT with Issues read/write):
  ```
  claude mcp add-json --scope user github '{"type":"http","url":"https://api.githubcopilot.com/mcp","headers":{"Authorization":"Bearer <YOUR_GITHUB_PAT>"}}'
  ```
- **Jira** (Atlassian Rovo MCP server, OAuth):
  ```
  claude mcp add --transport http --scope user atlassian https://mcp.atlassian.com/v2/mcp
  ```
  Then run `/mcp` in a session to authenticate.

## Repo layout
```
.claude-plugin/plugin.json        plugin manifest
.claude-plugin/marketplace.json   marketplace (this repo is both)
skills/<name>/SKILL.md            init, brainstorm, roadmap, backlog, stories, sync
skills/sync/{github,jira}.md      tracker-specific reference, loaded on demand
scripts/pp.py                     offline helper: validate | plan | set-tracker | archive
schemas/                          workflow.schema.json, item-frontmatter.md
templates/                        roadmap.md, epic.md, user-story.md
workflow.example.yaml             annotated config example
```
