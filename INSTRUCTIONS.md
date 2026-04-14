# LLM Wiki — Universal Operating Instructions

> This file is the universal version of the wiki schema, readable by any LLM regardless of IDE.
> For Claude Code specifically, see `CLAUDE.md` (identical content, recognized automatically).

---

## Your Role

You are operating an **LLM Wiki** — a persistent, structured knowledge base stored as markdown files. Your job is to maintain this wiki: ingest new sources, answer questions, cross-reference pages, and keep everything organized.

**On every new session:**
1. Read this file to understand the system
2. Read `index.md` to see what content exists
3. Read `log.md` for recent activity
4. Build a short list of relevant `wiki/entities/`, `wiki/concepts/`, and `wiki/queries/` pages before answering anything non-trivial

## Relevance Routing

When a user asks a question, do not jump straight into summaries or raw sources.

1. Read `index.md`
2. Route the request into the most relevant durable pages first:
   - `wiki/entities/` for project, product, company, tool, or person questions
   - `wiki/concepts/` for patterns, architecture, recurring bugs, workflows, or techniques
   - `wiki/queries/` for prior synthesis, naming normalization, or already-answered durable questions
3. Read `wiki/summaries/` only if the durable pages do not answer the question well enough
4. Read `sources/` only when the summaries are still insufficient or exact source wording matters

Use canonical project pages when names are noisy or ambiguous. For example, map naming variants through normalization/query pages before assuming they are separate products.

---

## Architecture

```
sources/           — Raw immutable documents (never edit these)
wiki/entities/     — Pages about people, orgs, tools, projects
wiki/concepts/     — Pages about ideas, patterns, techniques
wiki/summaries/    — Summaries of source documents
wiki/queries/      — Valuable answered questions saved as pages
index.md           — Master catalog of all wiki content
log.md             — Chronological record of all operations
```

---

## Page Format

Every wiki page must have YAML frontmatter:

```yaml
---
title: "Page Title"
type: entity | concept | summary | query
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: ["source-file.md"]
tags: [tag1, tag2]
status: active | stale | draft
---
```

Use `[[wiki-links]]` to cross-reference: `[[entities/person-name]]`, `[[concepts/idea-name]]`.

---

## Operations

### INGEST (process new source)
1. Save raw source to `sources/`
2. Read it thoroughly
3. Create summary in `wiki/summaries/`
4. Create/update entity pages in `wiki/entities/`
5. Create/update concept pages in `wiki/concepts/`
6. Add cross-references between related pages
7. Update `index.md`
8. Append to `log.md`

### QUERY (answer a question)
1. Read `index.md` to find relevant pages
2. Read the most relevant `entities/`, `concepts/`, and `queries/` pages first
3. Read summaries only if more detail is needed
4. Synthesize answer with citations
5. Optionally save as `wiki/queries/` page
6. Append to `log.md`

### LINT (health check)
1. Check for contradictions, stale pages, orphans, missing links, gaps
2. Fix what you can, flag what needs human input
3. Record in `log.md`

### INGEST-CHATS (process IDE chat history)
Ingest conversations from IDE chat histories into the wiki. Extracts knowledge from past sessions.

**Trigger phrases:** "Ingest chats", "Absorb chats", "Process chat history"

```bash
# List available chats
python3 tools/ingest-chats.py list

# Refresh memory incrementally
./refresh-memory

# Ingest all chats
python3 tools/ingest-chats.py ingest --all

# Ingest current project only
python3 tools/ingest-chats.py ingest --current

# Ingest specific project
python3 tools/ingest-chats.py ingest --project "project-name"
```

The tool saves raw transcripts to `sources/chats/` and summaries to `wiki/summaries/`.
After running, read the summaries and create entity/concept pages from the extracted knowledge.

Supports: Claude Code, Cursor, Windsurf, Continue, Cline.

### REFRESH-MEMORY
Use `./refresh-memory` for the one-command maintenance cycle:
1. discover chats
2. ingest only new or updated sessions
3. rebuild `index.md`
4. append a refresh entry to `log.md`

---

## On Every New Session

1. Read this file to understand the system
2. Read `index.md` to see what content exists
3. Scan `log.md` for recent activity
4. Check for un-ingested chats: `python3 tools/ingest-chats.py list`
5. If relevant new chats exist, offer to ingest them
6. Identify the smallest relevant set of `entities/`, `concepts/`, and `queries/` pages for the current request
7. **Auto-context:** The wiki is your long-term memory. Prefer durable pages first, summaries second, raw sources last.

---

## Rules

- **Sources are immutable** — never edit files in `sources/`
- **Wiki pages are living** — update freely with new info
- **Cross-reference aggressively** — connections compound value
- **Cite sources** — every claim traces to a source
- **Flag uncertainty** — mark unclear/contradictory info explicitly
- **Filenames**: lowercase, hyphen-separated: `my-topic.md`

---

## Log Format

```markdown
## [YYYY-MM-DD] TYPE | Description
Details of what happened.
Pages touched: [[page1]], [[page2]]
```

Types: `INGEST`, `QUERY`, `LINT`, `INIT`, `UPDATE`
