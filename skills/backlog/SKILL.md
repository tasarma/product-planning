---
name: backlog
description: (Stub) Turn roadmap items into prioritized epic files (one per epic) scored with the project's prioritization framework. Third stage of the product-planning workflow.
disable-model-invocation: true
---

# Backlog / epics (stub, not implemented yet)

**Status:** stub. Tell the user this stage isn't implemented yet, show the TODO list below, and stop.

## Purpose
Turn the Now and Next items on the roadmap into epic files, each scored with the configured prioritization framework, plus an ordered backlog index.

## Inputs
- `product/workflow.yaml`: `prioritization`, `ids.epic_prefix`, `paths.roadmap`, `paths.backlog`, and `templates.epic`. If the file is missing, stop and point the user to `/product-planning:init`.
- The roadmap at `paths.roadmap`. If it's missing, stop and suggest `/product-planning:roadmap`.
- Template: `templates.epic` if set, otherwise `${CLAUDE_PLUGIN_ROOT}/templates/epic.md`.
- Frontmatter contract: `${CLAUDE_PLUGIN_ROOT}/schemas/item-frontmatter.md` (Epic section).
- Writing style: before you write any prose, follow `${CLAUDE_PLUGIN_ROOT}/references/apply-writing-style.md`. Don't copy the rules here.

## Outputs
- `<paths.backlog>/<EPIC-NNN>-<slug>.md`, one per epic, created with `status: draft`
- `<paths.backlog>/README.md`, the epics ordered by priority

## TODO
- [ ] Ask for the scoring inputs for each epic (e.g. RICE: reach, impact, confidence, effort). Never invent them.
- [ ] Assign the next free id, checking both `paths.backlog` and `paths.archive`
- [ ] Generate the priority-ordered README index
- [ ] Explain `status: approved` and the review flow (draft → review → approved)
- [ ] Validate with `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pp.py plan .`
- [ ] Hand off to `/product-planning:stories`
