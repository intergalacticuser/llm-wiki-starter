# LLM Wiki — Schema & Operating Instructions

> A persistent, compounding knowledge base maintained by LLMs.
> Based on the LLM Wiki pattern by Andrej Karpathy (2026).

---

## What This Is

This is an **LLM Wiki** — a structured, interlinked collection of markdown files that serves as persistent memory across sessions. Instead of starting from scratch each conversation, the LLM reads this wiki to recall context, entities, concepts, and prior work.

The wiki sits between raw source documents and the LLM. It is a **compounding artifact**: cross-references are already built, contradictions flagged, knowledge organized.

---

## Three-Layer Architecture

```
Layer 1: sources/        — Raw, immutable source documents (articles, papers, data, images)
Layer 2: wiki/           — LLM-generated markdown (summaries, entity pages, concept pages, queries)
Layer 3: AGENTS.md       — This file. Schema, conventions, workflows.
```

---

## Directory Structure

```
llm wiki/
├── AGENTS.md              # This file — schema & operating instructions
├── INSTRUCTIONS.md        # Universal version for any LLM/IDE
├── index.md               # Content catalog organized by category
├── log.md                 # Append-only chronological record
├── README.md              # Setup guide for humans
│
├── sources/               # Layer 1: Raw immutable source documents
│   ├── *.md               # Articles, papers converted to markdown
│   ├── *.pdf              # Original PDFs
│   ├── *.png / *.jpg      # Images, diagrams
│   └── *.csv / *.json     # Data files
│
├── wiki/                  # Layer 2: LLM-generated content
│   ├── entities/          # Pages about people, orgs, tools, projects
│   │   └── *.md
│   ├── concepts/          # Pages about ideas, patterns, techniques
│   │   └── *.md
│   ├── summaries/         # Source document summaries
│   │   └── *.md
│   └── queries/           # Answered questions filed as wiki pages
│       └── *.md
│
├── tools/                 # Automation scripts
│   ├── ingest-chats.py    # Chat history ingestion (Python)
│   ├── refresh-memory.py  # Incremental memory refresh + index rebuild
│   └── wiki-ingest-chats.sh  # Shell wrapper for chat ingestion
│
├── .cursorrules           # Schema for Cursor IDE
├── .clinerules            # Schema for Cline
├── .github/
│   └── copilot-instructions.md  # Schema for GitHub Copilot
└── .windsurfrules         # Schema for Windsurf IDE
```

---

## Page Format

Every wiki page uses this frontmatter structure:

```markdown
---
title: "Page Title"
type: entity | concept | summary | query
created: YYYY-MM-DD
updated: YYYY-MM-DD
sources: ["source-file.md"]       # Which sources informed this page
tags: [tag1, tag2]
status: active | stale | draft
---

# Page Title

Page content in markdown. Use [[wiki-links]] to cross-reference other pages.

## See Also
- [[Related Page 1]]
- [[Related Page 2]]
```

### Wiki-Link Convention

Use `[[page-name]]` to link between wiki pages. The page-name is the filename without `.md` extension and without the directory prefix. When referencing, include the path hint:

- `[[entities/andrej-karpathy]]` — link to an entity page
- `[[concepts/rag-vs-wiki]]` — link to a concept page
- `[[summaries/source-article-name]]` — link to a summary

---

## Core Operations

### 1. INGEST — Process a New Source

When the user provides a new source document or asks to ingest content:

1. **Save** the raw source to `sources/` (if not already there)
2. **Read** the source thoroughly
3. **Create a summary** in `wiki/summaries/` with key takeaways, claims, and data
4. **Create or update entity pages** in `wiki/entities/` for people, orgs, tools mentioned
5. **Create or update concept pages** in `wiki/concepts/` for ideas, patterns, techniques
6. **Update cross-references** — add `[[wiki-links]]` between related pages
7. **Update `index.md`** — add new pages to the catalog under appropriate categories
8. **Append to `log.md`** — record the ingest with timestamp

A single source may touch 10-15 wiki pages. This is normal and expected.

### 2. QUERY — Answer a Question

When the user asks a question:

1. **Read `index.md`** to find relevant wiki pages
2. **Route by page type first**:
   - `wiki/entities/` for projects, products, companies, tools, and people
   - `wiki/concepts/` for recurring patterns, architecture, workflows, and failure modes
   - `wiki/queries/` for prior syntheses, normalization rules, and durable question pages
3. **Read summaries only if needed** after the durable pages
4. **Read raw sources only if needed** for exact detail, ambiguity resolution, or citation depth
5. **Synthesize an answer** with citations to wiki pages and original sources
6. **Optionally file the answer** as a new page in `wiki/queries/` if it has lasting value
7. **Append to `log.md`** — record the query

### 3. LINT — Health Check

Periodically (or when asked), audit the wiki for:

- **Contradictions** between pages — flag and resolve
- **Stale claims** — mark pages that may be outdated
- **Orphan pages** — pages with no incoming links
- **Missing cross-references** — pages that should link to each other but don't
- **Data gaps** — topics mentioned but not yet covered
- **Index drift** — pages that exist but aren't in `index.md`

Record lint results in `log.md`.

### 4. INGEST-CHATS — Process IDE Chat History

Ingest conversations from IDE chat histories into the wiki. This extracts knowledge from past sessions so it persists across conversations.

**Trigger phrases:** "Ingest chats", "Absorb chats", "Process chat history", "Засосать чаты"

**Using the built-in tool:**

```bash
# List all available chats across all IDEs
python3 tools/ingest-chats.py list

# Refresh memory incrementally (discover -> ingest new/updated -> rebuild index)
./refresh-memory

# Ingest ALL chats from all IDEs
python3 tools/ingest-chats.py ingest --all

# Ingest only current project's chats
python3 tools/ingest-chats.py ingest --current

# Ingest specific project
python3 tools/ingest-chats.py ingest --project "project-name"

# Ingest one specific chat file
python3 tools/ingest-chats.py ingest --chat /path/to/file.jsonl

# Filter by IDE
python3 tools/ingest-chats.py ingest --all --ide codex
```

**What it does:**
1. Finds conversation files from IDE storage (Codex, Cursor, Windsurf, Continue, Cline)
2. Extracts all user and assistant messages
3. Saves raw transcript to `sources/chats/` (immutable)
4. Creates a summary page in `wiki/summaries/` with key topics and initial request
5. Updates `log.md` with the ingestion record

**After running the tool**, the LLM should:
1. Read the generated summaries in `wiki/summaries/chat-*.md`
2. Extract key decisions, patterns, entities, and concepts
3. Create/update entity and concept pages as needed
4. Update `index.md` with new pages
5. Add cross-references between related pages

### 4a. REFRESH-MEMORY — Incremental Memory Refresh

Use `./refresh-memory` when you want a one-command refresh cycle:

1. Discover available chat sessions
2. Ingest only new or updated conversations
3. Rebuild `index.md`
4. Append a refresh record to `log.md`

Examples:

```bash
./refresh-memory
./refresh-memory --ide codex
./refresh-memory --current
./refresh-memory --project "mind-circle"
```

**Supported IDE chat storage locations:**

| IDE | Storage Path | Format |
|-----|-------------|--------|
| Codex | `~/.Codex/sessions/**/*.jsonl` | JSONL |
| Cursor | `~/Library/Application Support/Cursor/User/workspaceStorage/` | SQLite |
| Windsurf | `~/Library/Application Support/Windsurf/User/workspaceStorage/` | SQLite |
| Continue | `~/.continue/sessions/` | JSON |
| Cline | VS Code globalStorage `saoudrizwan.Codex-dev/` | JSON |

### 5. REVIEW — Summarize Wiki State

When asked "what do we know about X" or "review the wiki":

1. Read `index.md` for overview
2. Read `log.md` for recent activity
3. Read the most relevant `entities/`, `concepts/`, and `queries/` pages before opening summaries
4. Provide a structured summary of wiki contents, recent changes, and gaps

### 6. SESSION START — Relevance Routing For New Chats

When a new chat starts in this repository:

1. Read this file (`AGENTS.md`)
2. Read `index.md`
3. Read `log.md`
4. Build a short candidate set of relevant pages in `wiki/entities/`, `wiki/concepts/`, and `wiki/queries/`
5. If the project name is noisy or ambiguous, use normalization/query pages to map it to a canonical entity first
6. Only after that, open `wiki/summaries/` or `sources/` as needed

This routing is mandatory for non-trivial questions. Do not answer from scratch if the wiki already contains relevant durable memory.

---

## Naming Conventions

- **Filenames**: lowercase, hyphens for spaces: `andrej-karpathy.md`, `transformer-architecture.md`
- **Summaries**: match the source name: `sources/attention-paper.pdf` → `wiki/summaries/attention-paper.md`
- **Entities**: use the most common name: `openai.md`, `andrej-karpathy.md`
- **Concepts**: use descriptive names: `attention-mechanism.md`, `rag-vs-wiki.md`
- **Queries**: use question format: `how-does-attention-work.md`

---

## Log Format

`log.md` uses this format for parseability:

```markdown
## [YYYY-MM-DD] INGEST | Source: filename.md
Summary of what was ingested and which wiki pages were created/updated.
Pages touched: [[page1]], [[page2]], [[page3]]

## [YYYY-MM-DD] QUERY | Question text
Brief answer summary. See [[queries/question-page]] for full answer.

## [YYYY-MM-DD] LINT | Health check
Findings: N contradictions, N stale pages, N orphans, N gaps.
Actions taken: ...
```

---

## Important Principles

1. **Sources are immutable.** Never edit files in `sources/`. They are the ground truth.
2. **Wiki pages are living documents.** Update them freely as new information arrives.
3. **Cross-reference aggressively.** The value compounds through connections.
4. **Cite sources.** Every claim in the wiki should trace back to a source.
5. **Flag uncertainty.** If something is unclear or contradictory, say so explicitly.
6. **Compounding value.** Good answers become new wiki pages. The wiki grows smarter over time.
7. **Human curates, LLM maintains.** The human decides what to ingest and what questions matter. The LLM handles the bookkeeping.

---

## On Every New Session

When starting a new conversation with this wiki:

1. Read this file (`AGENTS.md`) to understand the system
2. Read `index.md` to know what's in the wiki
3. Scan `log.md` for recent activity
4. Check if there are un-ingested chats: run `python3 tools/ingest-chats.py list` to see recent sessions
5. If relevant new chats exist, offer to ingest them
6. Build a small relevance shortlist from `wiki/entities/`, `wiki/concepts/`, and `wiki/queries/`
7. You are now ready to ingest, query, or lint

**Auto-context loading:** When the user asks a question, always check `index.md` first. If the wiki has relevant pages, read durable memory pages before summaries, and summaries before raw sources. The wiki is your long-term memory — use it.

---

## Tooling Integration

This wiki is designed to work with:

- **Obsidian** — for human browsing, graph view, and web clipper for ingesting articles
- **Git** — for version history (init a repo in this directory)
- **Any LLM IDE** — Codex, Cursor, Copilot, Windsurf, Cline, Aider, etc.
- **qmd** — optional hybrid BM25/vector search CLI for large wikis
- **Marp** — for generating slide decks from wiki content
- **Dataview** (Obsidian plugin) — for querying page frontmatter

---

## Quick Reference

| Command | What to do |
|---------|-----------|
| "Ingest this" | Run INGEST operation on provided source |
| "What do we know about X?" | Run QUERY operation |
| "Lint the wiki" | Run LINT operation |
| "Review the wiki" | Run REVIEW operation |
| "Add to sources" | Save file to `sources/`, don't process yet |
| "Update index" | Rebuild `index.md` from current wiki pages |
| "Refresh memory" | Run `./refresh-memory` to ingest new/updated chats and rebuild the index |
| "Ingest chats" / "Засосать чаты" | Run INGEST-CHATS: process IDE conversation history |
| "Ingest all chats" | Run INGEST-CHATS with `--all` flag |
| "Ingest this chat" | Run INGEST-CHATS with `--current` flag |
| "List chats" | Run `python3 tools/ingest-chats.py list` |
