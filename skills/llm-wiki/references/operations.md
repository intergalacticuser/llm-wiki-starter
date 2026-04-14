# LLM Wiki Operations

## Repo signals

This skill is meant for repositories that look like a wiki-backed memory system, usually with:

- `AGENTS.md`
- `index.md`
- `log.md`
- `sources/`
- `wiki/`
- repo-local maintenance tools such as `./refresh-memory`

## Preferred command ladder

Use the smallest command that matches the task.

### Daily refresh

```bash
./refresh-memory
```

Useful variants:

```bash
./refresh-memory --ide codex
./refresh-memory --ide claude-code
./refresh-memory --current
./refresh-memory --project "my-project"
```

### Chat inspection and targeted ingest

```bash
python3 tools/ingest-chats.py list
python3 tools/ingest-chats.py ingest --all
python3 tools/ingest-chats.py ingest --current
python3 tools/ingest-chats.py ingest --project "my-project"
python3 tools/ingest-chats.py ingest --chat /path/to/chat.jsonl
```

### Product-family analysis

```bash
python3 tools/analyze-product-families.py
```

Use this when one product may be spread across renamed folders, copied workspaces, or versioned directories.

## Query routing order

Do not answer from scratch if the wiki already contains durable memory.

Use this order:

1. `index.md`
2. `log.md`
3. relevant `wiki/entities/`
4. relevant `wiki/concepts/`
5. relevant `wiki/queries/`
6. `wiki/summaries/`
7. `sources/`

Treat folder names and chat titles as clues, not as final truth, when deciding product identity.

## Maintenance checklist

After ingest or major synthesis work, check whether the repo expects updates to:

- durable pages in `wiki/entities/`, `wiki/concepts/`, and `wiki/queries/`
- cross-links between related pages
- `index.md`
- `log.md`

## Public-safe publishing checklist

Before helping publish or export the wiki:

- exclude raw chats unless they were intentionally prepared for public release
- exclude secrets, tokens, and local absolute paths
- exclude deployment details, server addresses, and internal notes
- review derived memory pages for sensitive summaries, not just raw sources

## Roadmap-aware workflow

If the repository has a public roadmap and changelog:

- treat `ROADMAP.md` as the planning source of truth
- treat GitHub issues and milestones as the working backlog
- keep repo docs and GitHub state aligned when changes are made on purpose
