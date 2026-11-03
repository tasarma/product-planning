# Apply the writing style

Do these steps before you write prose into any product file.

1. Read `writing_style` from `product/workflow.yaml`. If the key is not there, use `ste`.
2. If the value is `none`, do not apply style rules. Go to step 4.
3. Read `${CLAUDE_PLUGIN_ROOT}/references/writing-styles/<writing_style>.md` and follow its rules.
4. Read the glossary at `glossary` in workflow.yaml (default `product/glossary.md`), if the file exists. Use each term exactly as written. Never use a word from its "Do not use" column. This step applies with every style, also `none`.
5. Write the content.

Apply the rules to prose only. Do not change code, identifiers, config keys, frontmatter, quoted text, or wording that the user gave inside quotes. Template headings and the `**Given**`/`**When**`/`**Then**` markers stay as they are.
