# Story splitting reference

A story is a **vertical slice**: a complete, working piece of a feature that a user can use. A developer can build it, and a reviewer can review it, in about one PR.

## Walking skeleton first
The first story of an epic is the thinnest end-to-end path that a user can use. It includes the setup that this path needs (project structure, a table, a route). There is no separate "setup" story.

## Heuristics (try them in this order)
1. **Workflow step.** One story for each step that the user sees as separate. Example: upload a file → map the columns → import.
2. **Happy path, then other paths.** The happy path ships first. Validation, error and empty states become later stories. Exception: error handling that keeps the happy path safe (for example, no data loss) stays in the happy-path story.
3. **Business rule variants.** Example: a flat discount first, then a percentage discount.
4. **CRUD operation.** Create and view go together, because you can't verify create without view. Then edit, then delete.
5. **User role.** One story for each persona, when the permissions or flows are different.
6. **Data or input variants.** Example: CSV first, then XLSX. Only when the scope includes both.
7. **Simple, then full.** Example: a manual trigger first, then a schedule. Only when the scope includes both.
8. **Non-functional requirements.** Performance or scale work gets its own story, only when the brief or the epic states the requirement.

## Do not split by
- technical layer: "database", "API", "UI"
- "setup", "polish", "refactor" or "tests" stories
- pieces that exist only to make a story smaller (filler)

## Size rule: a story is too big when one of these is true
- It has more than 6 acceptance criteria, or more than one happy path.
- The "I want" line needs "and".
- More than one persona acts in it.
- It covers more than one workflow step that the user sees as separate.
- It adds more than one new external integration.
- Its estimate is in the top third of `estimation.scale`.
- You can't describe the PR in one sentence. As a rough guide, the PR changes more than about 400 lines.

## Keep it as one story when
- a piece is not usable or testable alone
- a split needs throwaway code to make a piece work
- the pieces always ship together
- the pieces repeat the same acceptance criteria

Then write the reason in the story's Notes: `Kept as one story because …`.

## Coverage and overlap checks
- **Gap:** an In-scope item of the epic has no story. Add a story.
- **Orphan:** a story maps to no In-scope item. Remove it, or ask the user. Never keep it silently.
- **Overlap:** two stories have the same Given and When. Merge them, or move the shared criteria into one story.
- **Out of scope:** never add a feature, a "nice-to-have" or extra polish that the epic and the brief do not include.

## Trade-offs
- **Small stories against overhead:** small is the default, but every story must be usable alone. The "keep it as one story" rule stops artificial pieces.
- **Full coverage against story count:** the two-way coverage table removes gaps and orphans. The overlap check removes filler.
