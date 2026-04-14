---
name: "llm-wiki-refresh"
description: "Use when the user wants a one-command memory refresh for an LLM Wiki repository, especially to run `./refresh-memory`, pull new chat sessions, rebuild the index, and summarize what changed."
---

# LLM Wiki Refresh

Use this skill for the daily maintenance loop in an LLM Wiki repository.

## Workflow

1. Confirm the repository looks like an LLM Wiki and check for `./refresh-memory`.
2. Prefer `./refresh-memory` as the primary command.
3. If the user asks for scope, pass the matching flags such as `--ide codex`, `--ide claude-code`, `--current`, or `--project "name"`.
4. After refresh, read `log.md`, `index.md`, and any obviously affected durable pages.
5. Summarize what changed, what was ingested, and whether follow-up promotion into `entities`, `concepts`, or `queries` is needed.

## Fallback

If `./refresh-memory` is missing but `tools/ingest-chats.py` exists, fall back to the smaller ingest commands and say that you are doing so.

## Shared reference

For the common command ladder and public-safety checklist, read `../llm-wiki/references/operations.md`.

## Example prompts

- `Use $llm-wiki-refresh to refresh this wiki and tell me what changed.`
- `Use $llm-wiki-refresh to refresh only Codex sessions in this workspace.`
