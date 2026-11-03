---
name: init
description: Create and validate product/workflow.yaml for the product-planning workflow by interviewing the user. Use when starting product planning in a new project, or when workflow.yaml is missing or invalid.
argument-hint: "[answers or notes, optional]"
disable-model-invocation: true
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pp.py *) Bash(mkdir -p *)
---

# Initialize product/workflow.yaml

Creates the per-project config that every other product-planning skill reads.
Schema: `${CLAUDE_PLUGIN_ROOT}/schemas/workflow.schema.json`. Annotated example: `${CLAUDE_PLUGIN_ROOT}/workflow.example.yaml`.

## Rules
- **Never guess required values.** If an answer is missing or unclear, ask. Defaults are allowed only for fields marked *default* in [questions.md](questions.md), and you must say which defaults you used.
- If the user supplied answers in `$ARGUMENTS`, use them and ask only for what is still missing.
- **No secrets.** Never write tokens, passwords, or URLs containing credentials. If the user offers one, refuse it and explain that auth comes from the MCP server.

## Steps
1. If `product/workflow.yaml` already exists: run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pp.py validate product/workflow.yaml`, show the result, and ask whether to **edit** it, **overwrite** it, or **stop**. Don't change anything until the user answers.
2. Read [questions.md](questions.md). Ask the questions in the groups listed there, using AskUserQuestion when it's available, with at most 4 questions per call. Free-text answers (name, goal, personas, repo) can be asked in plain chat.
3. Write `product/workflow.yaml`. Follow the structure and comment style of `workflow.example.yaml`, but include only the fields that were answered or defaulted. Keep the header comment that says the file must contain no secrets.
4. Validate it with `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pp.py validate product/workflow.yaml`. If it fails, fix what you can from the user's own answers. Ask the user about anything else, then validate again. Repeat until the output says `OK`.
5. Create the folders: `mkdir -p` the `research`, `backlog`, `stories` and `archive` paths, plus the parent folder of the `roadmap` path.
6. Finish with:
   - a short summary of the config, listing any defaults applied
   - the MCP setup command for the tracker, from the "MCP setup" section of [questions.md](questions.md), unless `tracker.type` is `none`
   - next step: `/product-planning:brainstorm`
