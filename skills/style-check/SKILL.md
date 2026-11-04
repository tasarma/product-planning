---
name: style-check
description: Check product docs against the project's writing style (writing_style in product/workflow.yaml) and glossary. Report long sentences, passive voice, glossary conflicts, inconsistent terms and long paragraphs, then fix them only after the user says yes.
argument-hint: "[file or folder]"
disable-model-invocation: true
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pp.py style-check *) Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pp.py plan *)
---

# Style check

Arguments: `$ARGUMENTS`, a file or a folder. If there are no arguments, the script checks `paths.research`, `paths.roadmap`, `paths.backlog` and `paths.stories` from `product/workflow.yaml`.

Run every command from the project root.

## Rules
- Never change code blocks, inline code, frontmatter, blockquotes, or text inside quotes. The script masks these parts. You must not edit them either.
- Do not change the meaning. Do not change the template headings or the `**Given**`/`**When**`/`**Then**` markers.
- Do not edit any file until the user replies **yes**.

## 1. Run the script
Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pp.py style-check $ARGUMENTS --json`.
- The script reads `writing_style` and `glossary` from the config. It reports `long-sentence`, `long-paragraph`, `glossary` and `passive?` items, each with a line number.
- Exit code 1 means it found issues. Exit code 2 means the config is invalid or there is nothing to check: show the message and stop.
- If the style is `none`, say "writing_style is none: only glossary checks run".

## 2. Add the judgment checks
Read each file that the script reported on, or that has prose.
- **Passive voice**: the `passive?` items are only candidates. Keep the real passives and drop the false matches (for example "is open"). Add any real passives that the script missed. Skip this check if the style is `none`.
- **Inconsistent terms**: find two or more words that name the same thing (for example "user", "customer" and "member" for one persona). If the glossary has a term for it, use the glossary term as the fix. Otherwise, use the word that occurs most often.
- Read the active style file, `${CLAUDE_PLUGIN_ROOT}/references/writing-styles/<style>.md`, for the rules that you check by judgment.

## 3. Report
For each file, show one table:

| Line | Issue | Detail |
|---|---|---|
| 12 | Long sentence | 31 words, limit 25 (description) |

The issue types are: long sentence, long paragraph, passive voice, glossary conflict, inconsistent term. End with the totals. Then ask: *"Fix these N issues in M files? Reply **yes** to continue."* Stop if the answer is anything other than an explicit yes.

## 4. Fix (only after yes)
1. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pp.py style-check <files> --protected` and keep the output.
2. Edit only the prose that has an issue. Follow the active style file and the glossary. The plugin's style hook also checks each edit. If it stops an edit, the fix added a new issue: fix that text and edit again.
3. Run the `--protected` command again. Each file must have the same hash as before. If a hash changed, undo your edits to that file and report it as "not fixed: protected text changed".
4. If you changed files in `paths.backlog` or `paths.stories`, run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/pp.py plan .` and confirm that no item has a new error.
5. Run the check from step 1 again.

## 5. Summary
Show one table: file | issues before | issues after | lines changed. Below the table, list the issues that are not fixed and give the reason for each one.
