# Jira reference (sync)

These are the tools of the Atlassian Rovo MCP server. Tool names can change, so find them by what they do and check each schema before you call it. The names known when this was written are in brackets.

| Need | Tool (known name) |
|---|---|
| Create issue | create Jira issue (`createJiraIssue`) |
| Update issue | edit Jira issue (`editJiraIssue`) |
| Read issue | get Jira issue (`getJiraIssue`) |
| Field metadata | issue-type metadata with fields (`getJiraIssueTypeMetaWithFields`) |
| Site / cloud id | Pass `tracker.jira.site` (e.g. `yourteam.atlassian.net`) as `cloudId`. Call accessible-resources (`getAccessibleAtlassianResources`) only if the tool rejects the hostname |

## Before the first write (once per run)
Fetch the field metadata for both configured issue types in `tracker.jira.project_key` and check:
- that the issue types exist (`issue_types.epic`, `issue_types.story`)
- that `fields.acceptance_criteria`, if it's a `customfield_*`, and `fields.story_points` exist on the story create screen

If one is missing, stop before any write. Show what's missing and tell the user to fix `workflow.yaml`.

## Mapping
- **summary / description**: take them from the plan's `payload`. The descriptions are markdown, and the Rovo MCP server converts markdown to Jira format. If a tool only accepts ADF, convert the headings, bullet lists, bold and italics one-to-one. Keep each Given/When/Then step as its own bullet.
- **issue type**: `payload.issue_type`. **Project**: `payload.project_key`.
- **fields**: `payload.fields` holds the acceptance criteria field (when it isn't `description`) and the story points field, both already keyed by field id. If the AC field is a rich-text field, send it as markdown or ADF in the same way as the description.
- `{{parent_ref}}` becomes the epic key, e.g. `PLAN-7`.
- `tracker_id` is the issue key (`PLAN-12`). `tracker_url` is `https://<site>/browse/<key>`.

## Epic linking
- `epic_link: parent` sets `parent: {"key": "<epic key>"}` on create and on update.
- `epic_link: customfield_NNNNN` sets that field to the epic key.

## Updates
Use edit-issue with the summary, description and fields from the plan. Don't change status or workflow transitions, assignee, or sprint, because those belong to the tracker.
