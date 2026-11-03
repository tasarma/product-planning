---
name: stories
description: (Stub) Break an epic into user stories with Given/When/Then acceptance criteria, using the shared story frontmatter. Fourth stage of the product-planning workflow.
argument-hint: "[epic id]"
disable-model-invocation: true
---

# User stories (stub, not implemented yet)

**Status:** stub. Tell the user this stage isn't implemented yet, show the TODO list below, and stop.

## Purpose
Split one epic into small, independently shippable user stories. Each story has `As a / I want / so that` and Given/When/Then acceptance criteria.

## Inputs
- `product/workflow.yaml`: `users`, `constraints`, `estimation`, `ids.story_prefix`, `definition_of_ready`, `paths.backlog`, `paths.stories`, and `templates.story`. If the file is missing, stop and point the user to `/product-planning:init`.
- `$ARGUMENTS`: an epic id such as `EPIC-001`. If it's missing, list the epics in `paths.backlog` and ask which one.
- Template: `templates.story` if set, otherwise `${CLAUDE_PLUGIN_ROOT}/templates/user-story.md`.
- Frontmatter contract: `${CLAUDE_PLUGIN_ROOT}/schemas/item-frontmatter.md` (Story section). The fields are `id`, `title`, `epic`, `status` (`draft|review|approved`), `priority`, `estimate`, `tracker_id`, `tracker_url`.
- Writing style: before you write any prose, follow `${CLAUDE_PLUGIN_ROOT}/references/apply-writing-style.md`. Don't copy the rules here.

## Outputs
- `<paths.stories>/<US-NNN>-<slug>.md`, one per story, created with `status: draft` and `tracker_id`/`tracker_url` set to `null`
- The story ids appended to the epic's `## Stories` section

## TODO
- [ ] INVEST check for each story (independent, negotiable, valuable, estimable, small, testable)
- [ ] Acceptance criteria as `### ACn` plus **Given**/**When**/**Then** bullets, in the exact format `pp.py` parses
- [ ] Personas in "As a" must come from `users`
- [ ] Definition of Ready checklist: only suggest `approved` when every item passes
- [ ] Estimates must come from `estimation.scale`, and you ask for them instead of guessing
- [ ] Never write `tracker_id` or `tracker_url` (sync owns them)
- [ ] Validate with `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pp.py plan .`
- [ ] Hand off to `/product-planning:sync --dry-run`
