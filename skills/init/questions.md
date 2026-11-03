# init: questions and mapping

Ask the groups in order. **R** means required: always ask for it and never invent a value. *default* means you can propose the default and use it if the user accepts it or doesn't care.

## Group 1: Product (R)
| Question | Field | Notes |
|---|---|---|
| Product name? | `product.name` | R |
| One-line goal: who it helps, and with what outcome? | `product.goal` | R, single line |

## Group 2: Users and constraints
| Question | Field | Notes |
|---|---|---|
| Who are the main personas? Give a name, a short description, and their goals. | `users[]` | Ask for at least one. If the user truly has none yet, leave it out and warn that the stories stage will ask again |
| What constraints apply: compliance, regulatory, technical, business? | `constraints[]` | Optional. `type` must be one of compliance, regulatory, technical, business, other |

## Group 3: Planning method
| Question | Field | Options |
|---|---|---|
| Which prioritization framework? | `prioritization` | R: `RICE`, `MoSCoW`, `WSJF`, `value-effort` |
| How do you estimate? | `estimation.unit` | *default* `story_points`: `story_points`, `t-shirt`, `none` |
| What's your estimation scale? | `estimation.scale` | *default* `[1,2,3,5,8,13]` for points, `[XS,S,M,L,XL]` for t-shirt. Leave it out when unit is `none` |
| Id prefixes for epics and stories? | `ids.epic_prefix`, `ids.story_prefix` | *default* `EPIC`, `US`. Uppercase only |
| Definition of Ready / Done items? | `definition_of_ready[]`, `definition_of_done[]` | Optional. Offer the example lists from `workflow.example.yaml` |
| Custom file locations? | `paths.*` | *default*: research `product/research`, roadmap `product/roadmap.md`, backlog `product/backlog`, stories `product/stories`, archive `product/archive` |

## Group 4: Tracker
| Question | Field | Notes |
|---|---|---|
| Where should approved items be synced? | `tracker.type` | R: `github`, `jira`, `none` |

If **github**:
| Question | Field | Notes |
|---|---|---|
| Repository (`owner/name`)? | `tracker.github.repo` | R |
| Labels for epics, stories, and extra labels for every issue? | `tracker.github.labels` | *default*: `epic`, `user-story`, no extras |
| Milestone number? | `tracker.github.milestone` | Optional |
| GitHub Project name? | `tracker.github.project` | Optional |

If **jira**:
| Question | Field | Notes |
|---|---|---|
| Site hostname, e.g. `yourteam.atlassian.net`? | `tracker.jira.site` | R. Hostname only: no `https://`, no credentials |
| Project key? | `tracker.jira.project_key` | R, uppercase |
| Issue type names for epic and story? | `tracker.jira.issue_types` | *default*: `Epic`, `Story` |
| Where should acceptance criteria go? | `tracker.jira.fields.acceptance_criteria` | *default* `description`, or `customfield_NNNNN` |
| Story points field id? | `tracker.jira.fields.story_points` | Optional `customfield_NNNNN`. Often `customfield_10016` on Jira Cloud, but **ask** |
| How are stories linked to epics? | `tracker.jira.epic_link` | *default* `parent`. Older company-managed projects use the Epic Link field `customfield_NNNNN` |

## MCP setup
Print the command that matches `tracker.type`:

- **github** (remote GitHub MCP server, authenticated with a personal access token that has Issues read/write access on the repo):
  ```
  claude mcp add-json --scope user github '{"type":"http","url":"https://api.githubcopilot.com/mcp","headers":{"Authorization":"Bearer <YOUR_GITHUB_PAT>"}}'
  ```
- **jira** (Atlassian Rovo MCP server, authenticated with OAuth):
  ```
  claude mcp add --transport http --scope user atlassian https://mcp.atlassian.com/v2/mcp
  ```
  Then run `/mcp` in a session, choose `atlassian`, and authenticate in the browser.

Then restart Claude Code, or run `/mcp`, and confirm the server shows as connected.
