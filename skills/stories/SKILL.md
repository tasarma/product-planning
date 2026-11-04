---
name: stories
description: Break one epic into small vertical-slice user stories with Given/When/Then acceptance criteria, each about one PR. Checks that the stories cover the epic's scope with no gaps, no overlap and nothing extra, and makes traceability visible in the files. Fourth stage of the product-planning workflow.
argument-hint: "[epic id]"
disable-model-invocation: true
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pp.py plan *)
---

# User stories

Split one epic into user stories. Each story is a vertical slice that a developer can build, and a reviewer can review, in about one PR. Together, the stories cover the epic's In-scope list completely, and they add nothing outside it.

## Inputs
- `product/workflow.yaml`: `users`, `constraints`, `estimation`, `ids.story_prefix`, `definition_of_ready`, `paths.research`, `paths.backlog`, `paths.stories`, `paths.archive`, `templates.story`. If the file is missing, stop and point the user to `/product-planning:init`.
- `$ARGUMENTS`: an epic id such as `EPIC-001`. If it's missing, list the epics in `paths.backlog` and ask which one.
- The epic file, and `<paths.research>/brief.md` for the definitions of the features that the epic traces to.
- The stories that already exist for this epic.
- Template: `templates.story` if set, otherwise `${CLAUDE_PLUGIN_ROOT}/templates/user-story.md`.
- Splitting rules: [splitting.md](splitting.md). Read it before step 3.
- Frontmatter contract: `${CLAUDE_PLUGIN_ROOT}/schemas/item-frontmatter.md` (Story section).
- Writing style: before you write any prose, follow `${CLAUDE_PLUGIN_ROOT}/references/apply-writing-style.md`. Don't copy the rules here.

## Outputs
- `<paths.stories>/<US-NNN>-<slug>.md`, one file for each story, with `status: draft` and `tracker_id`/`tracker_url` set to `null`.
- The coverage table in the epic's `## Stories` section.

## Rules
- **Traceability must be visible.** A developer or reviewer must be able to check coverage by reading the files:
  - Each story has a `**Traces to:**` line: the epic id, the brief feature id, and the In-scope item.
  - The epic's `## Stories` section is a table. Each In-scope item has a row that lists its story ids.
- **Scope comes from the epic.** Don't add speculative features, "nice-to-haves" or extra polish. If you think something is missing from the scope, ask the user. Don't add a story for it.
- **Personas** in "As a" come from `users` in workflow.yaml.
- **Acceptance criteria** use `### ACn: <name>` and then `- **Given**`, `- **When**`, `- **Then**` bullets (`And`/`But` allowed). `pp.py` parses this exact format.
- **Out of scope** in each story names what the story does not do, and the story id that does it.
- **Estimates** come from `estimation.scale`. Ask the user for them. Don't guess.
- **Never write** `tracker_id` or `tracker_url`. Sync owns them.
- **Ids:** use the next free `<ids.story_prefix>-NNN`. Check `paths.stories` and `paths.archive`.

## Steps
1. **Load.** Read the config, the epic, the brief, and the epic's existing stories. Stop and send the user to `/product-planning:backlog` if one of these is true:
   - The epic has no `**Traces to:**` line with brief feature ids.
   - The epic has no In-scope list.
2. **Map the workflow.** List the steps that the user takes through the epic, in order. This list is the backbone of the stories.
3. **Draft the walking skeleton.** The first story is the thinnest end-to-end path that a user can use. See [splitting.md](splitting.md).
4. **Split.** Apply the heuristics in [splitting.md](splitting.md) until every story passes the size rule. If a story must stay large, write the reason in its Notes.
5. **Check coverage in both directions.**
   - Each In-scope item has at least one story. If an item has no story, add one.
   - Each story maps to an In-scope item. If a story maps to nothing, remove it or ask the user.
   - Existing stories count. Don't duplicate them.
6. **Check overlap.** If two stories have the same Given and When, merge them, or move the shared criteria into one story.
7. **Show the plan before you write.** Show one table with these columns: id, title, In-scope item, AC count, depends on, size note. Show the coverage table under it. Ask the user for changes and for the estimates.
8. **Write.** Write the story files from the template. Then replace the epic's `## Stories` section with the coverage table.
9. **Check readiness.** For each story, check `definition_of_ready`. Suggest `status: approved` only when every item passes. Never change the status without the user's approval.
10. **Validate.** Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pp.py plan .`. Fix the errors and run it again.
11. **Hand off.** Summarize the stories and the coverage. Next step: `/product-planning:sync --dry-run`.

## Coverage across the whole product
This skill checks coverage for one epic. The full chain is: brief feature `F#` → roadmap → epic → story. A feature in Later or Not doing has no epic yet, so it has no stories yet. The brief is complete for a horizon when every Now and Next epic is covered.
