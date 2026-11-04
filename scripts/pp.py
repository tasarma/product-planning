#!/usr/bin/env python3
"""product-planning helper. Deterministic, offline. Never talks to a tracker.

Usage:
  pp.py validate <workflow.yaml>
  pp.py plan <project-root> [--json]
  pp.py set-tracker <file> <tracker_id> <tracker_url>
  pp.py archive <project-root> <story-file>...
  pp.py style-check [<file-or-folder>...] [--config product/workflow.yaml] [--json] [--protected]
  pp.py hook-style-check            (PreToolUse hook: reads hook JSON on stdin)

Requires python3 + PyYAML. Uses the `jsonschema` package for validation if
installed; otherwise a built-in validator for the subset of JSON Schema that
schemas/workflow.schema.json uses.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
from pathlib import Path

try:
    import yaml
    YAML_MISSING = False
except ImportError:  # pragma: no cover
    YAML_MISSING = True  # main() reports this; the hook fails open instead

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = PLUGIN_ROOT / "schemas" / "workflow.schema.json"
CONFIG_REL = Path("product") / "workflow.yaml"
STATUSES = ("draft", "review", "approved")
FOOTER = ("<sub>Synced one-way from `{file}` by product-planning. "
          "Edit the file, not this issue: tracker-side edits are overwritten on the next sync.</sub>")

# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #
_TYPES = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
}


def _fmt(path: list) -> str:
    out = ""
    for p in path:
        out += f"[{p}]" if isinstance(p, int) else (f".{p}" if out else str(p))
    return out or "(root)"


def _validate(node, schema: dict, path: list, errors: list) -> None:
    t = schema.get("type")
    if t is not None:
        types = t if isinstance(t, list) else [t]
        if not any(_TYPES[x](node) for x in types):
            errors.append(f"{_fmt(path)}: expected {' or '.join(types)}, got {type(node).__name__}")
            return
    if "const" in schema and node != schema["const"]:
        errors.append(f"{_fmt(path)}: must be {schema['const']!r}")
    if "enum" in schema and node not in schema["enum"]:
        errors.append(f"{_fmt(path)}: {node!r} is not one of {schema['enum']}")
    if isinstance(node, str):
        if len(node) < schema.get("minLength", 0):
            errors.append(f"{_fmt(path)}: must not be empty")
        if "pattern" in schema and not re.search(schema["pattern"], node):
            errors.append(f"{_fmt(path)}: {node!r} does not match pattern {schema['pattern']}")
    if isinstance(node, dict):
        for req in schema.get("required", []):
            if req not in node:
                errors.append(f"{_fmt(path + [req])}: required field is missing")
        props = schema.get("properties", {})
        for k, v in node.items():
            if k in props:
                _validate(v, props[k], path + [k], errors)
            elif schema.get("additionalProperties") is False:
                errors.append(f"{_fmt(path + [k])}: unknown field (allowed: {', '.join(props)})")
    if isinstance(node, list) and "items" in schema:
        for i, v in enumerate(node):
            _validate(v, schema["items"], path + [i], errors)
    for sub in schema.get("allOf", []):
        if "if" in sub:
            probe: list = []
            _validate(node, sub["if"], path, probe)
            branch = sub.get("then") if not probe else sub.get("else")
            if branch:
                _validate(node, branch, path, errors)
        else:
            _validate(node, sub, path, errors)


SECRET_VALUE = [
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"), "looks like a GitHub token"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}"), "looks like a GitHub fine-grained token"),
    (re.compile(r"\bATATT[A-Za-z0-9_\-=]{20,}"), "looks like an Atlassian API token"),
    (re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"), "looks like a Slack token"),
    (re.compile(r"[a-z][a-z0-9+.-]*://[^/\s:@]+:[^/\s@]+@"), "URL contains embedded credentials"),
    (re.compile(r"(?i)\b(token|api[_-]?key|password|secret)\s*[=:]\s*\S+"), "contains an inline credential"),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{16,}"), "contains a bearer token"),
]
SECRET_KEY = re.compile(r"(?i)^(token|access_token|api_key|apikey|password|passwd|secret|client_secret|pat)$")


def _scan_secrets(node, path: list, errors: list) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(k, str) and SECRET_KEY.match(k):
                errors.append(f"{_fmt(path + [k])}: secrets are not allowed in workflow.yaml "
                              "(auth comes from the MCP server)")
            _scan_secrets(v, path + [k], errors)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _scan_secrets(v, path + [i], errors)
    elif isinstance(node, str):
        for rx, why in SECRET_VALUE:
            if rx.search(node):
                errors.append(f"{_fmt(path)}: value {why}; remove it (auth comes from the MCP server)")
                break


def validate_config(cfg) -> list[str]:
    schema = json.loads(SCHEMA_PATH.read_text())
    errors: list[str] = []
    try:
        import jsonschema  # type: ignore

        v = jsonschema.Draft202012Validator(schema)
        for e in sorted(v.iter_errors(cfg), key=lambda e: list(e.absolute_path)):
            errors.append(f"{_fmt(list(e.absolute_path))}: {e.message}")
    except ImportError:
        _validate(cfg, schema, [], errors)
    _scan_secrets(cfg, [], errors)
    return errors


def load_config(path: Path) -> tuple[dict | None, list[str]]:
    if not path.is_file():
        return None, [f"{path}: file not found. Run /product-planning:init first."]
    try:
        cfg = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        return None, [f"{path}: invalid YAML: {e}"]
    if not isinstance(cfg, dict):
        return None, [f"{path}: top level must be a mapping"]
    errors = validate_config(cfg)
    return (None, errors) if errors else (with_defaults(cfg), [])


def _defaults_from(schema: dict, node: dict) -> None:
    for k, sub in schema.get("properties", {}).items():
        if "default" in sub and k not in node:
            node[k] = sub["default"]
        if sub.get("type") == "object" and sub.get("properties"):
            if k in node and isinstance(node[k], dict):
                _defaults_from(sub, node[k])
            elif k not in node and any("default" in s for s in sub["properties"].values()):
                node[k] = {}
                _defaults_from(sub, node[k])


def with_defaults(cfg: dict) -> dict:
    schema = json.loads(SCHEMA_PATH.read_text())
    cfg = json.loads(json.dumps(cfg))
    for key in ("paths", "ids", "estimation"):
        cfg.setdefault(key, {})
    _defaults_from(schema, cfg)
    tr = cfg["tracker"]
    tschema = schema["properties"]["tracker"]["properties"]
    if tr["type"] in ("github", "jira"):
        _defaults_from(tschema[tr["type"]], tr[tr["type"]])
    for k in ("definition_of_ready", "definition_of_done", "users", "constraints"):
        cfg.setdefault(k, [])
    return cfg


# --------------------------------------------------------------------------- #
# Item files
# --------------------------------------------------------------------------- #
FM_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)


def read_item(path: Path) -> tuple[dict | None, str, str | None]:
    text = path.read_text()
    m = FM_RE.match(text)
    if not m:
        return None, text, "no YAML frontmatter"
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        return None, text, f"invalid frontmatter YAML: {e}"
    if not isinstance(fm, dict):
        return None, text, "frontmatter must be a mapping"
    return fm, text[m.end():], None


def _sections(body: str) -> list[tuple[str, str]]:
    """Split markdown body into (heading, text) on '## ' headings. Heading '' = preamble."""
    out, head, buf = [], "", []
    for line in body.splitlines():
        if line.startswith("## "):
            out.append((head, "\n".join(buf).strip()))
            head, buf = line[3:].strip(), []
        else:
            buf.append(line)
    out.append((head, "\n".join(buf).strip()))
    return [(h, re.sub(r"<!--.*?-->", "", t, flags=re.S).strip()) for h, t in out]


GWT_RE = re.compile(r"^\s*(?:[-*]\s*)?(?:\[[ xX]\]\s*)?\**\s*(Given|When|Then|And|But)\b\**\s*:?\s*\**\s*(.+)$", re.I)


def parse_ac(text: str) -> list[dict]:
    scenarios: list[dict] = []
    cur = None
    for line in text.splitlines():
        if line.startswith("### "):
            cur = {"title": line[4:].strip(), "steps": []}
            scenarios.append(cur)
            continue
        m = GWT_RE.match(line)
        if m:
            if cur is None:
                cur = {"title": f"AC{len(scenarios) + 1}", "steps": []}
                scenarios.append(cur)
            cur["steps"].append((m.group(1).capitalize(), m.group(2).strip().rstrip("*").strip()))
    return [s for s in scenarios if s["steps"]]


def render_ac(scenarios: list[dict], checklist: bool) -> str:
    lines = []
    for i, s in enumerate(scenarios, 1):
        title = s["title"]
        lines.append(f"- [ ] **{title}**" if checklist else f"**{title}**")
        for kw, txt in s["steps"]:
            lines.append(f"  - **{kw}** {txt}" if checklist else f"- *{kw}* {txt}")
        if not checklist and i < len(scenarios):
            lines.append("")
    return "\n".join(lines)


def _is_ac(heading: str) -> bool:
    return heading.lower().startswith("acceptance criteria")


def _scan(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.rglob("*.md") if p.name.lower() != "readme.md")


# --------------------------------------------------------------------------- #
# Plan
# --------------------------------------------------------------------------- #
def build_plan(root: Path) -> dict:
    cfg, errors = load_config(root / CONFIG_REL)
    if errors:
        return {"ok": False, "config_errors": errors}
    tracker = cfg["tracker"]["type"]
    p = cfg["paths"]
    epic_pfx, story_pfx = cfg["ids"]["epic_prefix"], cfg["ids"]["story_prefix"]
    scale = cfg["estimation"].get("scale") or []
    unit = cfg["estimation"]["unit"]

    items: list[dict] = []
    seen: dict[str, str] = {}

    def load(kind: str, folder: Path, pfx: str) -> None:
        for f in _scan(folder):
            rel = f.relative_to(root).as_posix()
            fm, body, err = read_item(f)
            it = {"kind": kind, "file": rel, "errors": [], "fm": fm or {}, "body": body}
            if err:
                it["errors"].append(err)
            fm = fm or {}
            for k in ("id", "title", "status") + (("epic",) if kind == "story" else ()):
                if not fm.get(k):
                    it["errors"].append(f"missing `{k}`")
            iid = str(fm.get("id") or "")
            if iid and not re.fullmatch(rf"{pfx}-\d+", iid):
                it["errors"].append(f"id `{iid}` must look like {pfx}-001")
            if iid in seen:
                it["errors"].append(f"duplicate id `{iid}` (also in {seen[iid]})")
            elif iid:
                seen[iid] = rel
            if fm.get("status") and fm["status"] not in STATUSES:
                it["errors"].append(f"status `{fm['status']}` must be one of {', '.join(STATUSES)}")
            items.append(it)

    load("epic", root / p["backlog"], epic_pfx)
    load("story", root / p["stories"], story_pfx)

    archived: dict[str, str] = {}
    for f in _scan(root / p["archive"]):
        fm, _, _ = read_item(f)
        if fm and fm.get("id") and fm.get("tracker_id"):
            archived[str(fm["id"])] = f"{fm['tracker_id']} ({f.relative_to(root).as_posix()})"

    epics = {str(i["fm"].get("id")): i for i in items if i["kind"] == "epic"}
    tid_re = {"github": r"\d+", "jira": rf"{re.escape(cfg['tracker'].get('jira', {}).get('project_key', ''))}-\d+",
              "none": r".*"}[tracker]

    for it in items:
        fm = it["fm"]
        tid = fm.get("tracker_id")
        it.update(id=str(fm.get("id") or ""), title=str(fm.get("title") or ""),
                  status=fm.get("status"), tracker_id=None if tid in (None, "") else str(tid),
                  tracker_url=fm.get("tracker_url") or None)
        if it["tracker_id"] and not re.fullmatch(tid_re, it["tracker_id"].lstrip("#")):
            it["errors"].append(f"tracker_id `{it['tracker_id']}` doesn't look like a {tracker} id")
        if it["kind"] == "story":
            sections = _sections(it["body"])
            ac = next((t for h, t in sections if _is_ac(h)), "")
            it["ac"] = parse_ac(ac)
            est = fm.get("estimate")
            if unit != "none" and scale and est not in (None, "") and est not in scale:
                it["errors"].append(f"estimate `{est}` not in estimation.scale {scale}")
            if it["status"] == "approved":
                if not it["ac"]:
                    it["errors"].append("approved story has no Given/When/Then acceptance criteria")
                if unit != "none" and est in (None, ""):
                    it["errors"].append("approved story has no estimate")
            parent = epics.get(str(fm.get("epic")))
            it["parent_epic"] = str(fm.get("epic") or "") or None
            if fm.get("epic") and not parent:
                it["errors"].append(f"epic `{fm['epic']}` not found in {p['backlog']}")
            elif parent and it["status"] == "approved" and not parent["fm"].get("tracker_id") \
                    and parent["fm"].get("status") != "approved":
                it["errors"].append(f"parent epic `{parent['fm'].get('id')}` is not approved and not synced")
            it["parent_tracker_id"] = (str(parent["fm"]["tracker_id"]) if parent and parent["fm"].get("tracker_id")
                                       else None)
        if it["id"] in archived and not it["tracker_id"]:
            it["errors"].append(f"id `{it['id']}` was already synced and archived as {archived[it['id']]}; "
                                "use a new id or restore the archived file")

        if it["status"] != "approved":
            it["action"], it["reason"] = "skip", f"status: {it['status'] or 'missing'}"
            if it["errors"]:
                it["reason"] += f" (also: {'; '.join(it['errors'])})"
        elif it["errors"]:
            it["action"], it["reason"] = "error", "; ".join(it["errors"])
        elif tracker == "none":
            it["action"], it["reason"] = "skip", "tracker.type is none"
        else:
            it["action"] = "update" if it["tracker_id"] else "create"
            it["reason"] = f"has tracker_id {it['tracker_id']}" if it["tracker_id"] else "approved, not yet synced"
            it["payload"] = render_payload(it, cfg)

    items.sort(key=lambda i: (i["kind"] != "epic", i["id"]))
    for it in items:
        for k in ("fm", "body", "errors"):
            it.pop(k, None)
    counts = {a: sum(1 for i in items if i["action"] == a) for a in ("create", "update", "skip", "error")}
    return {"ok": True, "tracker": tracker, "target": _target(cfg), "counts": counts, "items": items}


def _target(cfg: dict) -> str:
    t = cfg["tracker"]
    if t["type"] == "github":
        return t["github"]["repo"]
    if t["type"] == "jira":
        return f"{t['jira']['site']} / {t['jira']['project_key']}"
    return "none"


def _payload(it: dict, cfg: dict, tracker: str, rel: str) -> dict:
    body_sections = [(h, t) for h, t in _sections(it["body"]) if t and not _is_ac(h)]
    gh = tracker == "github"
    parts = []
    for h, t in body_sections:
        parts.append(f"## {h}\n\n{t}" if h else t)
    ac_text = render_ac(it.get("ac", []), checklist=gh) if it["kind"] == "story" else ""
    dod = cfg["definition_of_done"] if it["kind"] == "story" else []
    dod_text = "\n".join(f"- [ ] {d}" if gh else f"- {d}" for d in dod)
    parent_line = ""
    if it["kind"] == "story" and it.get("parent_epic"):
        parent_line = f"Parent epic: {it['parent_epic']} ({{{{parent_ref}}}})"
    footer = FOOTER.format(file=rel) if gh else f"Synced one-way from {rel} by product-planning. Edit the file, not this issue."
    title = f"[{it['id']}] {it['title']}"

    if gh:
        g = cfg["tracker"]["github"]
        body = list(parts)
        if ac_text:
            body.append(f"## Acceptance criteria\n\n{ac_text}")
        if dod_text:
            body.append(f"## Definition of done\n\n{dod_text}")
        body.append("---")
        if parent_line:
            body.append(parent_line)
        body.append(footer)
        labels = [g["labels"]["epic"] if it["kind"] == "epic" else g["labels"]["story"]]
        labels += list(g["labels"].get("extra") or [])
        if it["kind"] == "story" and it.get("parent_epic"):
            labels.append(f"epic:{it['parent_epic']}")
        out = {"title": title, "body": "\n\n".join(body), "labels": labels}
        if g.get("milestone") is not None:
            out["milestone"] = g["milestone"]
        return out

    j = cfg["tracker"]["jira"]
    ac_field = j["fields"]["acceptance_criteria"]
    desc = list(parts)
    fields: dict = {}
    if ac_text:
        if ac_field == "description":
            desc.append(f"## Acceptance criteria\n\n{ac_text}")
        else:
            fields[ac_field] = ac_text
    if dod_text:
        desc.append(f"## Definition of done\n\n{dod_text}")
    desc.append("---")
    desc.append(footer)
    sp = j["fields"].get("story_points")
    if it["kind"] == "story" and sp:
        fields["__story_points_field"] = sp
    out = {"project_key": j["project_key"],
           "issue_type": j["issue_types"]["epic" if it["kind"] == "epic" else "story"],
           "summary": title, "description": "\n\n".join(desc), "fields": fields}
    if it["kind"] == "story" and it.get("parent_epic"):
        out["epic_link"] = j["epic_link"]
    return out


def render_payload(it: dict, cfg: dict) -> dict:
    """Build the tracker payload. Stories get a literal `{{parent_ref}}` that sync replaces
    with the parent epic's tracker reference (e.g. `#12` or `PLAN-7`) once it is known."""
    it["estimate"] = it["fm"].get("estimate")
    p = _payload(it, cfg, cfg["tracker"]["type"], it["file"])
    sp = p.get("fields", {}).pop("__story_points_field", None)
    if sp and isinstance(it["estimate"], (int, float)):
        p["fields"][sp] = it["estimate"]
    if it["kind"] == "story":
        p["estimate"] = it["estimate"]
    it.pop("estimate", None)
    return p


def _cell(s) -> str:
    return str(s if s not in (None, "") else "—").replace("|", "\\|").replace("\n", " ")


def print_table(plan: dict) -> None:
    if not plan["ok"]:
        print("workflow.yaml is invalid:")
        for e in plan["config_errors"]:
            print(f"  - {e}")
        return
    print(f"Tracker: {plan['tracker']} → {plan['target']}  (one-way: files → tracker)\n")
    print("| # | Kind | ID | Title | Parent | Action | Tracker ID | Reason |")
    print("|---|------|----|-------|--------|--------|------------|--------|")
    for n, i in enumerate(plan["items"], 1):
        parent = i.get("parent_epic")
        if parent and i.get("parent_tracker_id"):
            parent += f" ({i['parent_tracker_id']})"
        print(f"| {n} | {i['kind']} | {_cell(i['id'])} | {_cell(i['title'])} | {_cell(parent)} | "
              f"**{i['action']}** | {_cell(i['tracker_id'])} | {_cell(i['reason'])} |")
    c = plan["counts"]
    print(f"\nTotals: create {c['create']}, update {c['update']}, skip {c['skip']}, error {c['error']}")


# --------------------------------------------------------------------------- #
# Write-back and archive
# --------------------------------------------------------------------------- #
def set_tracker(path: Path, tid: str, url: str) -> None:
    text = path.read_text()
    m = FM_RE.match(text)
    if not m:
        sys.exit(f"ERROR: {path} has no frontmatter")
    fm_lines = m.group(1).split("\n")
    for key, val in (("tracker_id", tid), ("tracker_url", url)):
        line = f"{key}: {json.dumps(val)}"
        for i, l in enumerate(fm_lines):
            if re.match(rf"{key}\s*:", l):
                fm_lines[i] = line
                break
        else:
            fm_lines.append(line)
    new_fm = "\n".join(fm_lines)
    fm_check = yaml.safe_load(new_fm)
    assert str(fm_check["tracker_id"]) == tid and fm_check["tracker_url"] == url
    path.write_text(text[: m.start(1)] + new_fm + text[m.end(1):])
    print(f"OK {path}: tracker_id={tid} tracker_url={url}")


def archive(root: Path, files: list[str]) -> int:
    cfg, errors = load_config(root / CONFIG_REL)
    if errors:
        print("\n".join(errors))
        return 1
    stories_dir = (root / cfg["paths"]["stories"]).resolve()
    archive_dir = root / cfg["paths"]["archive"]
    rc = 0
    for f in files:
        src = (root / f).resolve() if not Path(f).is_absolute() else Path(f).resolve()
        try:
            rel = src.relative_to(stories_dir)
        except ValueError:
            print(f"SKIP {f}: not inside {cfg['paths']['stories']}")
            rc = 1
            continue
        fm, _, err = read_item(src) if src.is_file() else (None, "", "file not found")
        if err or not fm.get("tracker_id") or fm.get("status") != "approved":
            print(f"SKIP {f}: {err or 'not an approved, synced story (no tracker_id)'}")
            rc = 1
            continue
        dest = archive_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            print(f"SKIP {f}: {dest.relative_to(root)} already exists")
            rc = 1
            continue
        shutil.move(str(src), str(dest))
        print(f"MOVED {src.relative_to(root.resolve())} → {dest.relative_to(root)}")
    entry = cfg["paths"]["archive"].strip("/") + "/"
    gi = root / ".gitignore"
    lines = gi.read_text().splitlines() if gi.exists() else []
    if not any(l.strip().strip("/") == entry.strip("/") for l in lines):
        with gi.open("a") as fh:
            if lines and lines[-1].strip():
                fh.write("\n")
            fh.write(f"# product-planning: synced stories (local only)\n{entry}\n")
        print(f"ADDED `{entry}` to {gi.relative_to(root)}")
    else:
        print(f"OK `{entry}` already in .gitignore")
    return rc


# --------------------------------------------------------------------------- #
# Style check (heuristic; the style-check skill adds judgment on top)
# --------------------------------------------------------------------------- #
STYLE_DIR = PLUGIN_ROOT / "references" / "writing-styles"
DOC_PATH_KEYS = ("research", "roadmap", "backlog", "stories")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
LIST_RE = re.compile(r"^\s*(?:([-*+])|(\d+)[.)])\s+")
INLINE_CODE_RE = re.compile(r"`[^`]*`")
QUOTE_RE = re.compile(r"\"[^\"\n]*\"|“[^”\n]*”")
LINK_RE = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
WORD_RE = re.compile(r"[A-Za-z0-9][\w'’/.-]*")
ABBREV_RE = re.compile(r"\b(e\.g|i\.e|etc|vs|approx|incl)\.", re.I)
SENT_SPLIT_RE = re.compile(r"(?<=[.!?])[\"')\]]*\s+")
_IRREGULAR = ("made done sent shown given taken written built set put kept held found seen known told "
              "lost run read paid sold left brought bought caught thought chosen driven broken hidden "
              "forgotten begun drawn grown thrown worn torn spent sent lent meant felt dealt split shut")
_NOT_PARTICIPLE = {"when", "then", "even", "often", "open", "ten", "token", "seven", "eleven", "garden",
                   "kitchen", "children", "need", "red", "bed", "feed", "speed", "seed", "indeed",
                   "embed", "shed", "bleed", "breed", "hundred", "kindred", "sacred", "naked", "wicked"}
PASSIVE_RE = re.compile(r"\b(am|is|are|was|were|be|been|being|get|gets|got)\s+(?:\w+ly\s+)?"
                        r"(\w+(?:ed|en)|" + "|".join(_IRREGULAR.split()) + r")\b", re.I)


def _style_rules(style: str) -> dict:
    if style == "none":
        return {"name": "none"}
    f = STYLE_DIR / f"{style}.md"
    m = FM_RE.match(f.read_text()) if f.is_file() else None
    rules = (yaml.safe_load(m.group(1)) or {}) if m else {}
    rules.setdefault("name", style)
    return rules


def load_glossary(path: Path) -> list[dict]:
    """Rows of a markdown table: | Term | Definition | Do not use |."""
    terms = []
    if not path.is_file():
        return terms
    for line in path.read_text().splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 1 or not cells[0] or cells[0].lower() == "term" or set(cells[0]) <= set("-: "):
            continue
        avoid = [w.strip() for w in (cells[2] if len(cells) > 2 else "").split(",") if w.strip()]
        terms.append({"term": cells[0], "definition": cells[1] if len(cells) > 1 else "", "avoid": avoid})
    return terms


def _blocks(text: str) -> tuple[list[tuple[int, str, str]], list[str]]:
    """Classify lines. Returns ([(lineno, kind, masked_text)], protected_chunks).
    kind: prose | olist | ulist | cont | heading | table | blank. Skipped lines are not returned."""
    out, protected = [], []
    lines = text.splitlines()
    i = 0
    m = FM_RE.match(text)
    if m:
        n = m.group(0).count("\n") if m.group(0).endswith("\n") else m.group(0).count("\n") + 1
        protected.append(m.group(0))
        i = n
    fence = None
    in_comment = False
    for ln in range(i, len(lines)):
        raw = lines[ln]
        if fence:
            protected.append(raw)
            if raw.strip().startswith(fence):
                fence = None
            continue
        fm = FENCE_RE.match(raw)
        if fm:
            fence = fm.group(1)
            protected.append(raw)
            continue
        line = raw
        if in_comment:
            if "-->" not in line:
                continue
            line, in_comment = line.split("-->", 1)[1], False
        line = re.sub(r"<!--.*?-->", "", line)
        if "<!--" in line:
            line, in_comment = line.split("<!--", 1)[0], True
        if line.lstrip().startswith(">"):
            protected.append(raw)
            continue
        protected += INLINE_CODE_RE.findall(line) + QUOTE_RE.findall(line)
        masked = QUOTE_RE.sub("QUOTE", INLINE_CODE_RE.sub("CODE", line))
        masked = LINK_RE.sub(r"\1", masked)
        s = masked.strip()
        if not s:
            kind = "blank"
        elif s.startswith("#"):
            kind, masked = "heading", s.lstrip("#")
        elif s.startswith("|"):
            kind = "table"
        else:
            lm = LIST_RE.match(masked)
            if lm:
                kind = "olist" if lm.group(2) else "ulist"
                masked = masked[lm.end():]
            elif out and out[-1][1] in ("prose", "olist", "ulist", "cont"):
                kind = "cont"
            else:
                kind = "prose"
        out.append((ln + 1, kind, masked))
    return out, protected


def _paragraphs(blocks: list[tuple[int, str, str]]) -> list[dict]:
    paras, cur = [], None
    for ln, kind, txt in blocks:
        if kind in ("blank", "heading", "table"):
            cur = None
            continue
        if kind == "cont" and cur is not None:
            cur["parts"].append((ln, txt))
            continue
        cur = {"procedure": kind == "olist", "parts": [(ln, txt)]}
        paras.append(cur)
    return paras


def _sentences(para: dict) -> list[tuple[int, str]]:
    """Split a paragraph into (start_line, sentence)."""
    joined, starts = "", []
    for ln, txt in para["parts"]:
        clean = txt.replace("*", "").replace("_", " ").strip()
        if not clean:
            continue
        starts.append((len(joined), ln))
        joined += clean + " "
    safe = ABBREV_RE.sub(lambda m: m.group(1) + "\x00", joined)
    out, pos = [], 0
    for piece in SENT_SPLIT_RE.split(safe):
        seg = piece.replace("\x00", ".").strip()
        idx = joined.find(seg[:20], pos) if seg else -1
        if seg and WORD_RE.search(seg):
            off = idx if idx >= 0 else pos
            line = max((ln for o, ln in starts if o <= off), default=para["parts"][0][0])
            out.append((line, seg))
        pos += len(piece)
    return out


def check_file(path: Path, rules: dict, glossary: list[dict]) -> list[dict]:
    return check_text(path.read_text(), rules, glossary)


def check_text(text: str, rules: dict, glossary: list[dict]) -> list[dict]:
    issues = []
    blocks, _ = _blocks(text)
    style = rules["name"]
    for ln, kind, txt in blocks:
        for t in glossary:
            for w in t["avoid"]:
                for _ in re.finditer(r"(?<![\w-])" + re.escape(w) + r"(?![\w-])", txt, re.I):
                    issues.append({"line": ln, "issue": "glossary",
                                   "detail": f'"{w}" is on the do-not-use list: use "{t["term"]}"'})
    if style == "none":
        return sorted(issues, key=lambda i: i["line"])
    max_p, max_d = rules.get("max_words_procedure"), rules.get("max_words_description")
    max_s = rules.get("max_sentences_paragraph")
    for para in _paragraphs(blocks):
        sents = _sentences(para)
        limit = max_p if para["procedure"] else max_d
        for ln, s in sents:
            n = len(WORD_RE.findall(s))
            if limit and n > limit:
                kind = "procedure" if para["procedure"] else "description"
                short = s if len(s) <= 70 else s[:67] + "..."
                issues.append({"line": ln, "issue": "long-sentence",
                               "detail": f'{n} words ({kind}, limit {limit}): "{short}"'})
            for m in PASSIVE_RE.finditer(s):
                if m.group(2).lower() not in _NOT_PARTICIPLE:
                    issues.append({"line": ln, "issue": "passive?",
                                   "detail": f'"{m.group(0)}" (candidate: confirm by reading)'})
        if max_s and len(sents) > max_s:
            issues.append({"line": para["parts"][0][0], "issue": "long-paragraph",
                           "detail": f"{len(sents)} sentences (limit {max_s})"})
    return sorted(issues, key=lambda i: i["line"])


def _md_files(targets: list[Path]) -> list[Path]:
    files: list[Path] = []
    for t in targets:
        if t.is_dir():
            files += sorted(t.rglob("*.md"))
        elif t.is_file():
            files.append(t)
    return files


def style_check(args: list[str]) -> int:
    as_json = "--json" in args
    protected = "--protected" in args
    cfg_path = Path("product/workflow.yaml")
    if "--config" in args:
        i = args.index("--config")
        cfg_path = Path(args[i + 1])
        args = args[:i] + args[i + 2:]
    targets = [a for a in args if not a.startswith("--")]
    cfg: dict = {}
    if cfg_path.is_file():
        cfg, errors = load_config(cfg_path)
        if errors:
            print("INVALID config")
            for e in errors:
                print(f"  - {e}")
            return 2
    style = cfg.get("writing_style", "ste")
    gpath = Path(cfg.get("glossary", "product/glossary.md"))
    if not targets:
        paths = cfg.get("paths") or {}
        targets = [paths.get(k) for k in DOC_PATH_KEYS if paths.get(k)]
        if not targets:
            print("No paths given and no paths.* found in the config.")
            return 2
    files = [f for f in _md_files([Path(t) for t in targets])
             if not (gpath.is_file() and f.resolve() == gpath.resolve())]
    if protected:
        import hashlib
        for f in files:
            chunks = _blocks(f.read_text())[1]
            print(f"{hashlib.sha256(chr(10).join(chunks).encode()).hexdigest()}  {f}")
        return 0
    rules, glossary = _style_rules(style), load_glossary(gpath)
    report = [{"file": str(f), "issues": check_file(f, rules, glossary)} for f in files]
    total = sum(len(r["issues"]) for r in report)
    if as_json:
        print(json.dumps({"style": style, "glossary": str(gpath) if glossary else None,
                          "files": report, "total": total}, indent=2, ensure_ascii=False))
        return 1 if total else 0
    note = " (style none: glossary checks only)" if style == "none" else ""
    print(f"style: {style}{note} | glossary: {gpath if glossary else 'none'} | files: {len(files)}")
    for r in report:
        if not r["issues"]:
            print(f"\n{r['file']}: OK")
            continue
        print(f"\n{r['file']}: {len(r['issues'])} issue(s)")
        print(f"  {'line':>4}  {'issue':<15} detail")
        for i in r["issues"]:
            print(f"  {i['line']:>4}  {i['issue']:<15} {i['detail']}")
    print(f"\nTotal: {total} issue(s) in {sum(1 for r in report if r['issues'])} file(s)")
    return 1 if total else 0


# --------------------------------------------------------------------------- #
# PreToolUse hook: style-check a product doc before Write/Edit/MultiEdit lands
# --------------------------------------------------------------------------- #
HOOK_BLOCKING = ("long-sentence", "long-paragraph", "glossary")


def _apply_edits(old: str, edits: list[dict]) -> str | None:
    """Apply Edit/MultiEdit replacements. None if one doesn't match (the tool reports that)."""
    text = old
    for e in edits:
        o, n = e.get("old_string", ""), e.get("new_string", "")
        if not o or o not in text:
            return None
        text = text.replace(o, n) if e.get("replace_all") else text.replace(o, n, 1)
    return text


def _hook_target(cfg: dict, root: Path, target: Path) -> bool:
    if target.suffix.lower() != ".md" or target.name.lower() == "readme.md":
        return False
    gloss = (root / cfg.get("glossary", "product/glossary.md")).resolve()
    if target == gloss:
        return False
    for k in DOC_PATH_KEYS:
        p = (root / cfg["paths"][k]).resolve()
        if target == p or p in target.parents:
            return True
    return False


def hook_style_check(stdin: str) -> int:
    """Always exits 0. Prints a deny decision when the write adds style issues."""
    try:
        if YAML_MISSING:
            return 0
        data = json.loads(stdin)
        tool, ti = data.get("tool_name"), data.get("tool_input") or {}
        if tool not in ("Write", "Edit", "MultiEdit") or not ti.get("file_path"):
            return 0
        root = Path(data.get("cwd") or os.getcwd()).resolve()
        cfg, errors = load_config(root / CONFIG_REL)
        if errors or not cfg:
            return 0
        target = Path(ti["file_path"])
        target = (target if target.is_absolute() else root / target).resolve()
        if not _hook_target(cfg, root, target):
            return 0
        style = cfg.get("writing_style", "ste")
        glossary = load_glossary(root / cfg.get("glossary", "product/glossary.md"))
        if style == "none" and not glossary:
            return 0

        old = target.read_text() if target.is_file() else ""
        if tool == "Write":
            new = ti.get("content", "")
        else:
            edits = ti.get("edits") if tool == "MultiEdit" else [ti]
            new = _apply_edits(old, edits or [])
            if new is None:
                return 0

        rules = _style_rules(style)
        # Block only on issues the write adds. Compare counts, not lines: lines shift on edit.
        from collections import Counter
        before = Counter((i["issue"], i["detail"]) for i in check_text(old, rules, glossary)) if old else Counter()
        issues = []
        for i in check_text(new, rules, glossary):
            key = (i["issue"], i["detail"])
            if i["issue"] not in HOOK_BLOCKING:
                continue
            if before[key] > 0:
                before[key] -= 1
                continue
            issues.append(i)
        if not issues:
            return 0

        rel = target.relative_to(root).as_posix() if root in target.parents else str(target)
        lines = "\n".join(f"- line {i['line']} {i['issue']}: {i['detail']}" for i in issues)
        rules_ref = f"references/writing-styles/{style}.md" if style != "none" else "the glossary"
        reason = (f"Style check ({style}) blocked this write to {rel}. "
                  f"It adds {len(issues)} issue(s):\n{lines}\n"
                  "Rewrite only the affected prose and try again. Keep code, frontmatter, quoted text, "
                  f"template headings and the Given/When/Then markers unchanged. Rules: {rules_ref}.")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                 "permissionDecision": "deny",
                                                 "permissionDecisionReason": reason}}))
    except Exception:  # fail open: a broken hook must never stop writes
        return 0
    return 0


# --------------------------------------------------------------------------- #
def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] in ("-h", "--help"):
        print(__doc__)
        return 0
    cmd, args = argv[1], argv[2:]
    if cmd == "hook-style-check":
        return hook_style_check(sys.stdin.read())
    if YAML_MISSING:
        sys.exit("ERROR: PyYAML is required. Install it with: python3 -m pip install --user pyyaml")
    if cmd == "validate" and len(args) == 1:
        cfg, errors = load_config(Path(args[0]))
        if errors:
            print("INVALID")
            for e in errors:
                print(f"  - {e}")
            return 1
        t = cfg["tracker"]["type"]
        print(f"OK {args[0]} (tracker: {t}{' → ' + _target(cfg) if t != 'none' else ''})")
        return 0
    if cmd == "plan" and args:
        plan = build_plan(Path(args[0]))
        if "--json" in args:
            print(json.dumps(plan, indent=2, ensure_ascii=False))
        else:
            print_table(plan)
        return 0 if plan["ok"] else 1
    if cmd == "set-tracker" and len(args) == 3:
        set_tracker(Path(args[0]), args[1], args[2])
        return 0
    if cmd == "archive" and len(args) >= 2:
        return archive(Path(args[0]), args[1:])
    if cmd == "style-check":
        return style_check(args)
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
