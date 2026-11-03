---
name: roadmap
description: (Stub) Build or update a Now/Next/Later roadmap from research notes, using the project's prioritization framework. Second stage of the product-planning workflow.
disable-model-invocation: true
---

# Roadmap (stub, not implemented yet)

**Status:** stub. Tell the user this stage isn't implemented yet, show the TODO list below, and stop.

## Purpose
Turn the research notes into a Now/Next/Later roadmap made of themes and candidate epics, each with an outcome, a persona and a rationale.

## Inputs
- `product/workflow.yaml`: `product`, `users`, `constraints`, `prioritization`, `paths.research`, `paths.roadmap`, and `templates.roadmap`. If the file is missing, stop and point the user to `/product-planning:init`.
- Research notes in `paths.research`. If there are none, stop and suggest `/product-planning:brainstorm`.
- Template: `templates.roadmap` if set, otherwise `${CLAUDE_PLUGIN_ROOT}/templates/roadmap.md`.

## Outputs
- `paths.roadmap`, which is created or updated. Show a diff and ask before overwriting.

## TODO
- [ ] Cluster research findings into themes
- [ ] Place themes into Now/Next/Later, with the reasoning based on `prioritization`
- [ ] Add a "Not doing" list and the constraints that were considered
- [ ] Confirm with the user before writing
- [ ] Hand off to `/product-planning:backlog`
