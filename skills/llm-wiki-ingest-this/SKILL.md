---
name: "llm-wiki-ingest-this"
description: "Use when the user wants to ingest one pointed source or one current chat into an LLM Wiki repository, then summarize the extracted information and the resulting wiki updates."
---

# LLM Wiki Ingest This

Use this skill when the user means one source, one current chat, or one targeted ingest action.

## Workflow

1. Decide whether the target is:
   - the current project's recent chat history
   - one specific chat file
   - one newly added source file in the repo
2. For current chat history, prefer `python3 tools/ingest-chats.py ingest --current`.
3. For a specific chat file, use `python3 tools/ingest-chats.py ingest --chat /path/to/file`.
4. For a normal source document, follow the local ingest rules from `AGENTS.md` and update the wiki pages the repo expects.
5. After ingest, summarize the key extracted information, the touched pages, and any obvious follow-up memory work.

## Guardrail

Do not default to `--all` when the user clearly wants a single targeted ingest.

## Shared reference

For the common command ladder and routing order, read `../llm-wiki/references/operations.md`.

## Example prompts

- `Use $llm-wiki-ingest-this to ingest the current chat into the wiki.`
- `Use $llm-wiki-ingest-this to process this one source file and summarize what we learned.`
