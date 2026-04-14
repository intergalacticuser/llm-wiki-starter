---
name: "llm-wiki-analyze-families"
description: "Use when the user wants to find likely product families that span renamed folders, copied workspaces, or versioned directories inside an LLM Wiki repository."
---

# LLM Wiki Analyze Families

Use this skill when one product may be split across several chat names or workspace folders.

## Workflow

1. Confirm the repository looks like an LLM Wiki and check for `tools/analyze-product-families.py`.
2. Prefer `python3 tools/analyze-product-families.py` as the primary command.
3. After the run, read the new candidate report in `wiki/queries/`, then check `index.md` and `log.md`.
4. Distinguish between accepted canonical merges and review candidates.
5. If the user confirms that a candidate is truly one family, update the alias registry and the durable pages instead of leaving it as a floating candidate forever.

## Fallback

If the analyzer is missing, inspect `wiki/summaries/`, `wiki/entities/`, and any normalization pages manually and explain that you are falling back to manual family review.

## Shared reference

For the common command ladder and public-safety checklist, read `../llm-wiki/references/operations.md`.

## Example prompts

- `Use $llm-wiki-analyze-families to find products that may be split across different folders.`
- `Use $llm-wiki-analyze-families and tell me which candidates are strong enough to promote into canonical families.`
