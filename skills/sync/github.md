# GitHub reference (sync)

These are the tools of the official GitHub MCP server (`github/github-mcp-server`). The server name prefix can vary, e.g. `mcp__github__`. Check the real tool schemas before you call anything, because parameter names can change between server versions.

| Need | Tool | Notes |
|---|---|---|
| Create issue | `issue_write` (method `create`) | `owner`, `repo`, `title`, `body`, `labels`, optional `milestone` (number) |
| Update issue | `issue_write` (method `update`) | Same fields plus `issue_number`. Replace `body` and `labels` with the plan's values |
| Read issue | `issue_read` | Use it to confirm an issue for a `tracker_id` exists and to get its internal numeric `id` |
| Link sub-issue | `sub_issue_write` (method `add`) | Parent = epic `issue_number`; child = the story issue's **numeric id** (not its number). Get the id from the create response or `issue_read` |
| Labels | `label_write` | If a label in the plan doesn't exist and the create fails because of it, create the label, then retry once |

`owner/repo` comes from `tracker.github.repo`.

## Mapping
- **title / body / labels / milestone**: take them from the plan's `payload`. The body already contains the story text, the Acceptance criteria as a checklist of **Given/When/Then** bullets, the Definition of Done checklist, the parent reference, and a one-way-sync footer.
- `{{parent_ref}}` becomes `#<epic issue number>`.
- `tracker_id` is the issue **number** as a string, e.g. `"42"`. `tracker_url` is the issue's `html_url`.

## Epic linking (in order of preference)
1. **Sub-issue**: run `sub_issue_write` add, with the epic as parent and the story as child. On update, add it again only if `issue_read` shows the story has no parent yet. If the call errors with "already a sub-issue", treat it as success.
2. **Fallback** when `sub_issue_write` is unavailable or fails: the plan already puts an `epic:<EPIC-ID>` label on the story and a `Parent epic: … (#N)` line in its body. Note in the summary that the epic was linked by label and reference.

## Project and milestone
- `milestone` goes on `issue_write`.
- `tracker.github.project`: if the server has no tool for adding an issue to a Project, list the issue URLs in the summary so the user can add them by hand. Never fail an item over this.
