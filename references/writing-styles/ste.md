---
name: ste
max_words_procedure: 20
max_words_description: 25
max_sentences_paragraph: 6
---

# Writing style: STE-style

STE-style writing, based on ASD-STE100 (Simplified Technical English). This is **not** ASD-STE100 compliant: the official specification has a controlled dictionary, and this plugin does not include it.

## Scope
Apply these rules to prose only. Never change code, identifiers, config keys, file paths, log output, quoted text, or user-supplied wording inside quotes.

## Rules
**Sentences**
- Procedures (steps, instructions): 20 words or fewer per sentence.
- Descriptions: 25 words or fewer per sentence.
- Write one instruction per sentence.
- Use the active voice. Use the imperative for instructions.
- Use only simple tenses: present, past, future.
- Do not use an -ing form as a noun or a modifier when a simpler form exists.
- Keep articles (a, an, the).

**Words**
- One word, one meaning. Do not use synonyms for the same thing.
- Use common, short words. Do not use phrasal verbs ("set up" → "configure").
- Define a technical term the first time you use it.
- Use the terms from the project glossary exactly.

**Structure**
- Put the main point or the action first.
- One topic per paragraph. 6 sentences or fewer per paragraph.
- Use numbered lists for steps and bullets for items in no order.
- Put a warning before the step it applies to.

## Examples
**1. Instruction**
- Before: "The configuration file should be opened and the timeout value can then be changed if it is needed."
- After: "Open the configuration file. If necessary, change the timeout value."

**2. Description**
- Before: "Upon receiving the request, the processing of the payload is carried out by the worker, which then sends back a response."
- After: "The worker receives the request and processes the payload. Then it sends a response."

**3. Warning order**
- Before: "Run the migration. Note that you will lose data if you have not made a backup first."
- After: "WARNING: The migration can delete data. Make a backup before you continue." Then the step: "Run the migration."
