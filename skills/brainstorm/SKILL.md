---
name: brainstorm
description: (Stub) Brainstorm and research a product idea — problem, users, competitors, risks — and write notes to the configured research folder. First stage of the product-planning workflow.
argument-hint: "[idea or topic]"
disable-model-invocation: true
---

# Brainstorm / research (stub, not implemented yet)

**Status:** stub. Tell the user this stage isn't implemented yet, show the TODO list below, and stop. Don't improvise the stage.

## Purpose
Turn a raw idea into structured research notes: the problem, the personas, the alternatives and competitors, the risks and assumptions, and the open questions. These notes are the input to the roadmap.

## Inputs
- `product/workflow.yaml`: `product`, `users`, `constraints`, and `paths.research`. If the file is missing, stop and tell the user to run `/product-planning:init`.
- `$ARGUMENTS`: the idea or topic. If it's empty, ask for it.

## Outputs
- `<paths.research>/YYYY-MM-DD-<slug>.md`, one file per session
- `<paths.research>/README.md`, an index of the sessions

## TODO
- [ ] Define the research note template (problem, personas, jobs-to-be-done, alternatives, risks, assumptions, open questions)
- [ ] Interview flow: ask, don't guess; one topic at a time
- [ ] Optional web research with cited sources
- [ ] Check every idea against `constraints`
- [ ] Suggest updates to `users` in workflow.yaml and ask before writing them
- [ ] Hand off to `/product-planning:roadmap`
