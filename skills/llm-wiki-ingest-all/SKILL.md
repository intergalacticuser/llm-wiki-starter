---
name: "llm-wiki-ingest-all"
description: "Use when the user wants to ingest all available chat history or run a broad ingest pass across the LLM Wiki repository, then summarize the overall changes."
---

# LLM Wiki Ingest All

Use this skill when the user wants a wide ingest pass rather than a targeted one.

## Workflow

1. Confirm that the user really wants a broad ingest.
2. Prefer `python3 tools/ingest-chats.py ingest --all` for a full chat-history pass.
3. If the repo documents a broader non-chat ingest flow, follow the local rules rather than inventing a new one.
4. After ingest, read `log.md`, `index.md`, and the newly created summaries or durable pages.
5. Summarize the scale of the ingest, what clusters or themes appeared, and what follow-up grouping or promotion work is worth doing next.

## Guardrail

If the repository is large or the ingest could be expensive, mention the scope before running it, but do not silently downgrade to a partial ingest.

## Shared reference

For the common command ladder and routing order, read `../llm-wiki/references/operations.md`.

## Example prompts

- `Use $llm-wiki-ingest-all to pull all available chats into this wiki and summarize the result.`
- `Use $llm-wiki-ingest-all to do a broad ingest pass and tell me what clusters we should organize next.`
