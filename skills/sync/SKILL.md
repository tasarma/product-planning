---
name: sync
description: One-way sync of approved epics and user stories from product files to GitHub Issues or Jira, with a dry-run preview, idempotent create/update via tracker_id write-back, and epic linking. Use when the user wants to push the backlog to their tracker.
argument-hint: "[--dry-run]"
disable-model-invocation: true
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pp.py validate *) Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pp.py plan *) Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pp.py set-tracker *)
---

# Sync files → tracker (one-way)

Arguments: `$ARGUMENTS`. **Dry-run mode** is on if the arguments contain `--dry-run`.

This sync goes **one way only, from files to the tracker**. Never read tracker changes back into the files. The only file writes this skill makes are `tracker_id`/`tracker_url`, through `pp.py set-tracker`, and the optional archive in step 11.

Helper script: `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pp.py` (offline, deterministic). Run every command from the project root, always spelling out the full command.

## 1. Config
Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pp.py validate product/workflow.yaml`.
- If it prints **INVALID** or the file isn't found, show the errors and stop. Suggest `/product-planning:init`.
- If `tracker.type` is `none`, say "tracker.type is none, so there's nothing to sync" and stop.

## 2. MCP server
Look for the tracker tools in this session. If they're deferred, search for them with ToolSearch first.
- **github**: a tool whose name ends in `issue_write`, e.g. `mcp__github__issue_write`
- **jira**: a tool whose name contains `createJiraIssue`, or another Atlassian Jira create-issue tool

If the tools are missing, print the matching command and explain it, then **stop**. In dry-run mode, print it as a warning and continue, because a dry run never calls the tracker.
- github: `claude mcp add-json --scope user github '{"type":"http","url":"https://api.githubcopilot.com/mcp","headers":{"Authorization":"Bearer <YOUR_GITHUB_PAT>"}}'`
- jira: `claude mcp add --transport http --scope user atlassian https://mcp.atlassian.com/v2/mcp`, then run `/mcp` to authenticate

## 3–4. Build the plan
Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pp.py plan .` for the table and `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pp.py plan . --json` for the payloads. The script:
- reads the epics in `paths.backlog` and the stories in `paths.stories`
- marks each item **create** (approved, no `tracker_id`), **update** (approved, has `tracker_id`), **skip** (not approved), or **error** (approved but invalid, with the reason)
- already renders the issue title and body, the labels, and the Jira fields

Use those payloads exactly as given. Don't rewrite them.

## 5. Dry run and confirmation
Show the table exactly as the script printed it, followed by the totals.
- **Dry-run mode**: stop here with "Dry run complete. Nothing was sent to the tracker."
- If there's nothing to create or update, say so and stop.
- Otherwise ask: *"Proceed with N creates and M updates on <target>? Reply **yes** to continue."* Continue only on an explicit "yes". Anything else cancels the run.

## 6–8. Execute
Follow [github.md](github.md) or [jira.md](jira.md) for the exact tool calls. Process **epics first, then stories**, so every story's parent already exists.
- **create**: create the issue. **Immediately** run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pp.py set-tracker <file> <id> <url>` before moving to the next item, so an interrupted run can't produce duplicates.
- **update**: update the existing issue's title, body, labels and fields. Never create a new issue for an item that has a `tracker_id`. If the issue no longer exists, mark the item failed with "tracker_id not found". Don't recreate it.
- **Parent link**: replace `{{parent_ref}}` in the story body with the parent epic's reference (`#12` or `PLAN-7`) and link the issues as the reference file describes. If the epic was created earlier in this run, use its new id.
- **Acceptance criteria**: already rendered into the payload (body or configured field). Keep them as they are.
- If an item fails, record the error message and carry on with the rest. A story whose epic failed is also failed, with the reason "parent epic failed".

## 10. Summary
End with one table showing **Created / Updated / Skipped / Failed**. List each item with its id and tracker link, and give a reason for every skipped or failed item. Remind the user that the sync is one-way, so changes made in the tracker will be overwritten next time.

## 11. Optional archive
Do this only after a real run (not a dry run) in which at least one story was created or updated without failing. Ask:
*"Move the N synced story files to `<paths.archive>/` and add `<paths.archive>/` to .gitignore? Note: archived files, including their tracker_id, will then exist only on this machine. (yes/no)"*
On **yes**, run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pp.py archive . <story files that succeeded in this run>` and show the output. Only story files are archived. Epics stay where they are, because later stories link to them. On anything else, leave the files alone.
