# Item frontmatter (single source of truth)

Every epic file (in `paths.backlog`) and story file (in `paths.stories`) starts with YAML frontmatter.
Templates, the `backlog`/`stories` skills and `sync` all use these fields. `scripts/pp.py plan` enforces them.

## Story

| Field | Required | Values | Notes |
|---|---|---|---|
| `id` | yes | `<ids.story_prefix>-NNN` e.g. `US-001` | Unique across stories **and** `paths.archive` |
| `title` | yes | string | Synced as `[US-001] <title>` |
| `epic` | yes | an epic `id` | Must exist in `paths.backlog` |
| `status` | yes | `draft` \| `review` \| `approved` | Only `approved` is synced |
| `priority` | no | framework-specific | RICE score, MoSCoW bucket, WSJF score, or value/effort label |
| `estimate` | when approved* | a value from `estimation.scale` | *Not required if `estimation.unit: none` |
| `tracker_id` | no | GitHub issue number or Jira key | **Written by sync.** Present ⇒ update, absent ⇒ create |
| `tracker_url` | no | URL | **Written by sync** |

Body: must contain `## Acceptance criteria` with at least one scenario when approved.
Scenarios are `### <name>` followed by `- **Given** …`, `- **When** …`, `- **Then** …` (`And`/`But` allowed).

## Epic

| Field | Required | Values |
|---|---|---|
| `id` | yes | `<ids.epic_prefix>-NNN` e.g. `EPIC-001` |
| `title` | yes | string |
| `status` | yes | `draft` \| `review` \| `approved` |
| `priority` | no | framework-specific |
| `horizon` | no | `now` \| `next` \| `later` |
| `tracker_id`, `tracker_url` | no | **Written by sync** |

## File naming

`<id>-<kebab-slug>.md`, e.g. `product/stories/US-001-reset-password.md`. `README.md` files are ignored.
