#!/usr/bin/env python3
"""
LLM Wiki — Incremental memory refresh

One command to:
1. Discover available chats
2. Ingest only new or updated sessions
3. Rebuild index.md from the current durable wiki pages
4. Append a refresh entry to log.md
"""

from __future__ import annotations

import argparse
import importlib.util
import re
from collections import Counter
from datetime import datetime
from pathlib import Path


WIKI_ROOT = Path(__file__).resolve().parent.parent
INDEX_FILE = WIKI_ROOT / "index.md"
LOG_FILE = WIKI_ROOT / "log.md"
WIKI_DIR = WIKI_ROOT / "wiki"


def load_ingest_module():
    """Load tools/ingest-chats.py as a module despite the dash in the filename."""
    ingest_path = Path(__file__).resolve().parent / "ingest-chats.py"
    spec = importlib.util.spec_from_file_location("llm_wiki_ingest", ingest_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def parse_frontmatter(md_path: Path) -> dict:
    """Extract simple YAML frontmatter fields used by the wiki."""
    data = {}
    lines = md_path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return data

    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"')
    return data


def extract_page_summary(md_path: Path) -> str:
    """Use the first meaningful body paragraph as a compact description."""
    lines = md_path.read_text(encoding="utf-8").splitlines()
    frontmatter_markers_seen = 0
    paragraphs = []
    collected = []

    for line in lines:
        if frontmatter_markers_seen < 2:
            if line.strip() == "---":
                frontmatter_markers_seen += 1
            continue

        stripped = line.strip()
        if not stripped:
            if collected:
                paragraph = " ".join(collected).strip()
                if paragraph and not paragraph.startswith("#"):
                    paragraphs.append(paragraph)
                collected = []
            continue

        if stripped.startswith("#") or stripped.startswith("- "):
            if collected:
                paragraph = " ".join(collected).strip()
                if paragraph:
                    paragraphs.append(paragraph)
                collected = []
            continue

        collected.append(stripped)

    if collected:
        paragraph = " ".join(collected).strip()
        if paragraph:
            paragraphs.append(paragraph)

    summary = paragraphs[0] if paragraphs else ""
    summary = re.sub(r"\s+", " ", summary).strip()
    if len(summary) > 110:
        summary = summary[:107].rstrip() + "..."
    return summary


def build_section_lines(section_name: str, directory: Path) -> list[str]:
    """Build an index section from markdown files in a directory."""
    lines = [f"## {section_name}", ""]
    pages = sorted(directory.glob("*.md"))
    if not pages:
        lines.append("- None yet.")
        lines.append("")
        return lines

    for page in pages:
        title = parse_frontmatter(page).get("title", page.stem.replace("-", " ").title())
        summary = extract_page_summary(page)
        relative = page.relative_to(WIKI_DIR).with_suffix("")
        if summary:
            lines.append(f"- [[{relative.as_posix()}]] — {summary}")
        else:
            lines.append(f"- [[{relative.as_posix()}]] — {title}")
    lines.append("")
    return lines


def group_summary_clusters(summary_dir: Path) -> list[tuple[str, int]]:
    """Count repeated summary clusters from chat summary filenames."""
    counter = Counter()
    for page in summary_dir.glob("chat-*.md"):
        match = re.match(r"chat-(.+)_[0-9a-f]{8}\.md$", page.name)
        cluster = match.group(1) if match else page.stem
        counter[cluster] += 1
    return counter.most_common()


def rebuild_index() -> dict:
    """Regenerate index.md from current wiki pages."""
    entities_dir = WIKI_DIR / "entities"
    concepts_dir = WIKI_DIR / "concepts"
    summaries_dir = WIKI_DIR / "summaries"
    queries_dir = WIKI_DIR / "queries"
    sources_dir = WIKI_ROOT / "sources" / "chats"

    entity_pages = sorted(entities_dir.glob("*.md"))
    concept_pages = sorted(concepts_dir.glob("*.md"))
    summary_pages = sorted(summaries_dir.glob("*.md"))
    query_pages = sorted(queries_dir.glob("*.md"))
    raw_sources = sorted(sources_dir.glob("*.md"))
    clusters = group_summary_clusters(summaries_dir)

    lines = [
        "---",
        'title: "Wiki Index"',
        f"updated: {datetime.now().strftime('%Y-%m-%d')}",
        "---",
        "",
        "# Wiki Index",
        "",
        "This is the master catalog of the current LLM Wiki state.",
        "",
        "Read this file first when starting a session to know what durable memory pages already exist.",
        "",
        "---",
        "",
    ]

    lines.extend(build_section_lines("Entities", entities_dir))
    lines.append("---")
    lines.append("")
    lines.extend(build_section_lines("Concepts", concepts_dir))
    lines.append("---")
    lines.append("")
    lines.extend(build_section_lines("Queries", queries_dir))
    lines.append("---")
    lines.append("")
    lines.append("## Summary Clusters")
    lines.append("")
    lines.append("The full summary corpus lives in `wiki/summaries/`. The most repeated clusters right now are:")
    lines.append("")

    if clusters:
        for name, count in clusters[:14]:
            lines.append(f"- `{name}` — {count} session summaries")
        if len(clusters) > 14:
            remaining = ", ".join(f"`{name}`" for name, _ in clusters[14:28])
            lines.append("")
            lines.append(f"Smaller but still notable clusters include {remaining}.")
    else:
        lines.append("- No summary pages yet.")

    lines.extend([
        "",
        "---",
        "",
        "## Raw Sources",
        "",
        f"- `sources/chats/` — {len(raw_sources)} immutable chat transcripts imported from IDE history.",
        f"- `wiki/summaries/` — {len(summary_pages)} chat summary pages generated from those transcripts.",
        "",
        "---",
        "",
        "## Current Interpretation",
        "",
        "- Fresh sessions should route through `entities/`, `concepts/`, and `queries/` before falling back to summaries.",
        "- `wiki/summaries/` is the compression layer over raw transcripts, not the final memory layer.",
        "- The durable memory layer should keep growing as repeated decisions, bugs, and architecture patterns become clear.",
        "",
        "---",
        "",
        "## Statistics",
        "",
        f"- **Total wiki pages:** {len(entity_pages) + len(concept_pages) + len(summary_pages) + len(query_pages)}",
        f"- **Entities:** {len(entity_pages)}",
        f"- **Concepts:** {len(concept_pages)}",
        f"- **Summaries:** {len(summary_pages)}",
        f"- **Queries:** {len(query_pages)}",
        f"- **Sources:** {len(raw_sources)}",
        f"- **Last updated:** {datetime.now().strftime('%Y-%m-%d')}",
        "",
    ])

    INDEX_FILE.write_text("\n".join(lines), encoding="utf-8")
    return {
        "entities": len(entity_pages),
        "concepts": len(concept_pages),
        "summaries": len(summary_pages),
        "queries": len(query_pages),
        "sources": len(raw_sources),
        "total_pages": len(entity_pages) + len(concept_pages) + len(summary_pages) + len(query_pages),
    }


def insert_log_entry(action: str, details: str):
    """Insert a log entry near the top of log.md."""
    today = datetime.now().strftime("%Y-%m-%d")
    entry = f"\n## [{today}] {action}\n{details}\n"

    if LOG_FILE.exists():
        content = LOG_FILE.read_text(encoding="utf-8")
        marker = "---\n\n"
        pos = content.rfind(marker)
        if pos != -1:
            insert_at = pos + len(marker)
            content = content[:insert_at] + entry + content[insert_at:]
        else:
            content += entry
        LOG_FILE.write_text(content, encoding="utf-8")


def expected_output_paths(ingest, conv: dict) -> tuple[Path, Path]:
    """Match ingest-chats.py output naming logic."""
    project = ingest.safe_filename(conv["project"])
    session = conv["session_id"][:8]
    filename = f"{project}_{session}"
    raw_path = ingest.SOURCES_DIR / f"{filename}.md"
    summary_path = ingest.SUMMARIES_DIR / f"chat-{filename}.md"
    return raw_path, summary_path


def parse_chat_info(ingest, chat_info: dict) -> list[dict]:
    """Parse one discovered chat file into one or more conversations."""
    filepath = chat_info["path"]
    ide = chat_info["ide"]
    if ide == "codex":
        conv = ingest.parse_codex_jsonl(filepath)
        return [conv] if conv else []
    if ide == "claude-code":
        conv = ingest.parse_claude_code_jsonl(filepath)
        return [conv] if conv else []
    if ide in ("cursor", "windsurf"):
        return ingest.parse_cursor_vscdb(filepath)
    if ide == "continue":
        conv = ingest.parse_continue_json(filepath)
        return [conv] if conv else []
    return []


def needs_ingest(source_path: Path, raw_path: Path, summary_path: Path) -> bool:
    """Treat missing outputs or newer source sessions as needing refresh."""
    if not raw_path.exists() or not summary_path.exists():
        return True
    source_mtime = source_path.stat().st_mtime
    return raw_path.stat().st_mtime < source_mtime or summary_path.stat().st_mtime < source_mtime


def discover_target_chats(ingest, args) -> list[dict]:
    """Apply the same selection model as ingest-chats.py."""
    if args.current:
        return ingest.discover_all_chats(project_filter=str(Path.cwd()), ide_filter=args.ide)
    if args.project:
        return ingest.discover_all_chats(project_filter=args.project, ide_filter=args.ide)
    return ingest.discover_all_chats(ide_filter=args.ide)


def main():
    ingest = load_ingest_module()

    parser = argparse.ArgumentParser(description="Refresh LLM Wiki memory incrementally")
    parser.add_argument("--ide", type=str.lower, choices=["codex", "claude-code", "cursor", "windsurf", "continue", "cline"])
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--current", action="store_true", help="Refresh only chats matching the current working directory")
    scope.add_argument("--project", type=str, help="Refresh only chats for a specific project")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be ingested without writing files")
    args = parser.parse_args()

    discovered = discover_target_chats(ingest, args)
    if not discovered:
        print("No chat histories found for refresh.")
        return

    print(f"Discovered {len(discovered)} chat file(s).")
    ide_counts = Counter(chat["ide"] for chat in discovered)
    for ide, count in sorted(ide_counts.items()):
        print(f"  - {ide}: {count}")

    pending = []
    skipped_empty = 0

    for chat_info in discovered:
        for conv in parse_chat_info(ingest, chat_info):
            if not conv or not conv.get("messages"):
                skipped_empty += 1
                continue
            raw_path, summary_path = expected_output_paths(ingest, conv)
            if needs_ingest(chat_info["path"], raw_path, summary_path):
                pending.append((conv, raw_path, summary_path, chat_info))

    print(f"New or updated conversations to ingest: {len(pending)}")
    if skipped_empty:
        print(f"Skipped empty conversations: {skipped_empty}")

    processed = 0
    refreshed_summaries = []

    if not args.dry_run:
        for conv, raw_path, summary_path, chat_info in pending:
            ingest.save_chat(conv)
            processed += 1
            refreshed_summaries.append(summary_path.stem)
            print(f"  refreshed: {summary_path.name} ({chat_info['ide']})")

    stats = rebuild_index() if not args.dry_run else {}

    if not args.dry_run:
        detail_lines = [
            f"Discovered {len(discovered)} chat file(s) across selected IDE scope.",
            f"Ingested {processed} new or updated conversation(s).",
            f"Rebuilt index.md with {stats['total_pages']} total wiki pages.",
        ]
        if refreshed_summaries:
            detail_lines.append(
                "Summaries refreshed: " + ", ".join(f"[[summaries/{name}]]" for name in refreshed_summaries[:10])
            )
        insert_log_entry("REFRESH | Memory refresh", "\n".join(detail_lines))

    if args.dry_run:
        print("Dry run complete. No files were written.")
    else:
        print("Refresh complete.")
        print(f"Index rebuilt: {INDEX_FILE}")


if __name__ == "__main__":
    main()
