---
name: "llm-wiki-lint"
description: "Use when the user wants to health-check an LLM Wiki repository for issues such as orphan pages, index drift, broken links, stale structure, contradictions, or missing follow-up work."
---

# LLM Wiki Lint

Use this skill for wiki health checks.

## Workflow

1. If the repository has a dedicated lint command, use it.
2. Otherwise inspect the wiki structure directly:
   - compare `index.md` against the actual wiki folders
   - look for orphan pages and missing cross-links
   - flag stale summaries that were never promoted into durable pages
   - note contradictions or naming fragmentation when they are obvious
3. Summarize findings in severity order and separate real issues from open questions.
4. Suggest the smallest next maintenance actions that would improve the wiki most.

## Shared reference

For maintenance expectations and routing context, read `../llm-wiki/references/operations.md`.

## Example prompts

- `Use $llm-wiki-lint to check this wiki for drift and structural problems.`
- `Use $llm-wiki-lint to find orphan pages, missing links, and stale memory.`
