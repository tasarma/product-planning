---
id: US-000                # <ids.story_prefix>-NNN, unique across stories (and archive)
title: Short imperative title
epic: EPIC-000            # id of the parent epic in paths.backlog
status: draft             # draft | review | approved — only approved is synced
priority: null            # value in the project's prioritization framework (e.g. RICE score, Must/Should, WSJF)
estimate: null            # must be in estimation.scale (unless estimation.unit is none)
tracker_id: null          # written by /product-planning:sync — do not edit by hand
tracker_url: null         # written by /product-planning:sync — do not edit by hand
---

## Story

**As a** <persona from workflow.yaml users>
**I want** <capability>
**so that** <benefit>

**Traces to:** EPIC-000 → F0 (In-scope item: "<item from the epic>")

## Context

<!-- Why now, links to research/roadmap, constraints from workflow.yaml that apply. -->

## Acceptance criteria

### AC1: <scenario name>
- **Given** <precondition>
- **When** <action>
- **Then** <observable outcome>

### AC2: <scenario name>
- **Given** <precondition>
- **And** <another precondition>
- **When** <action>
- **Then** <observable outcome>

## Out of scope

<!-- What this story does not do, and the story id that does it. -->
- 

## Depends on

<!-- Story ids, or "None". -->
- None

## Notes

<!-- Open questions. If the story stays large, write: Kept as one story because ... -->
