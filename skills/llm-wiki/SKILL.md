---
name: "llm-wiki"
description: "Use when working in an LLM Wiki repository or when the user wants to ingest sources, refresh chat memory, answer from durable wiki pages, maintain index and log pages, or operate repo-local workflows such as `./refresh-memory` and `tools/ingest-chats.py`."
---

# LLM Wiki

Use this skill when the repository is acting as a persistent markdown memory system rather than a normal codebase.

Typical signals:

- the repo contains `AGENTS.md`, `INSTRUCTIONS.md`, `index.md`, `log.md`, `sources/`, and `wiki/`
- the user wants to ingest new sources or past chat sessions
- the user asks to refresh memory, review the wiki, lint it, or promote summaries into durable pages
- the user explicitly invokes `$llm-wiki`

If the repository does not match that shape, say so and fall back to the local instructions instead of pretending the skill applies.

## Core workflow

1. Read the local operating instructions first, especially `AGENTS.md` and `INSTRUCTIONS.md` if they exist.
2. For questions, route through the durable memory layer first:
   - `index.md`
   - `log.md`
   - relevant pages in `wiki/entities/`, `wiki/concepts/`, and `wiki/queries/`
   - summaries only when those pages are not enough
   - raw sources only when exact detail is still needed
3. For chat maintenance, prefer `./refresh-memory` when available. Use `tools/ingest-chats.py` only for targeted listing or ingest operations.
4. After ingest, update durable pages, cross-links, `index.md`, and `log.md` if the repository expects that maintenance flow.
5. If the repo includes `ROADMAP.md`, `CHANGELOG.md`, and GitHub milestones or issues, treat the repo docs as the planning surface and GitHub as the execution surface.
6. Before any public sharing, audit raw chats, summaries, derived pages, local paths, tokens, deployment details, and other sensitive context.

## What good use looks like

- refresh memory without reprocessing everything from scratch
- answer from the durable wiki before diving into transcripts
- turn repeated work into `entities`, `concepts`, and `queries`
- keep the public starter clean while private memory stays private

## References

- For command patterns and maintenance checklists, read `references/operations.md`.

## Example prompts

- `Use $llm-wiki to refresh memory for this workspace and summarize what changed.`
- `Use $llm-wiki to ingest this new source and update the durable pages it affects.`
- `Use $llm-wiki to review what we already know about this project before answering.`
