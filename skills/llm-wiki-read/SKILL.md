---
name: "llm-wiki-read"
description: "Use when the user wants to read or review what an LLM Wiki repository already knows about a topic, project, or problem before answering from scratch."
---

# LLM Wiki Read

Use this skill when the task is to read existing memory before answering.

## Workflow

1. Start with `index.md` and `log.md`.
2. Build a small relevant set from `wiki/entities/`, `wiki/concepts/`, and `wiki/queries/`.
3. Read summaries only when the durable pages are not enough.
4. Read raw sources only for exact detail, ambiguity resolution, or stronger citation support.
5. Answer from the durable memory layer first and say what the wiki already knows.

## Good fit

- `What do we know about X?`
- `Review the wiki`
- `Read the memory before answering`

## Shared reference

For the routing order and maintenance expectations, read `../llm-wiki/references/operations.md`.

## Example prompts

- `Use $llm-wiki-read to tell me what this wiki already knows about this project.`
- `Use $llm-wiki-read to review the existing memory before you answer my question.`
