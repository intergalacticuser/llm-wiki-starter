#!/usr/bin/env python3
"""
LLM Wiki — Product family analysis

Build a registry-backed, content-aware view of product identity across chat summaries.
This helps detect when the same product spans renamed folders, copied workspaces,
versioned directories, or different IDE sessions.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


WIKI_ROOT = Path(__file__).resolve().parent.parent
SUMMARY_DIR = WIKI_ROOT / "wiki" / "summaries"
QUERY_DIR = WIKI_ROOT / "wiki" / "queries"
ENTITY_DIR = WIKI_ROOT / "wiki" / "entities"
REGISTRY_FILE = Path(__file__).resolve().parent / "product-aliases.json"

FILENAME_RE = re.compile(r"chat-(.+)_[0-9a-f]{8}\.md$")
WORD_RE = re.compile(r"[a-z][a-z0-9-]{2,}|[а-яё][а-яё0-9-]{2,}", re.IGNORECASE)
LATIN_RE = re.compile(r"[a-z][a-z0-9-]{2,}", re.IGNORECASE)

STOPWORDS = {
    "about", "after", "again", "already", "also", "another", "because", "before",
    "any", "being", "been", "better", "between", "branch", "build", "built",
    "changes", "chat", "chats", "claude", "code", "codex", "commits", "context",
    "current", "current_date", "cwd", "debug", "deploy", "deployment", "different",
    "doing", "done", "environment", "feature", "features", "feedback", "file",
    "files", "final", "folder", "folders", "github", "great", "history", "html",
    "image", "images", "latest", "local", "logo", "main", "more", "need", "needs",
    "new", "next", "only", "page", "pages", "path", "please", "product",
    "project", "projects", "prompt", "recent", "release", "repo", "running", "same",
    "scratch", "server", "shell", "site", "some", "still", "summary", "system",
    "text", "then", "there", "these", "this", "timezone", "tool", "tools",
    "update", "status", "version", "versions", "web", "work", "working", "workspace",
    "workspaces", "would",
    "более", "будет", "будут", "важно", "весь", "все", "всё", "где", "говорю",
    "давай", "даже", "должен", "должна", "должно", "есть", "здесь", "значит",
    "именно", "как", "когда", "которые", "который", "можно", "нужно", "нужны",
    "него", "нее", "них", "наша", "наше", "нашего", "наши", "нашим", "нашем",
    "очень", "пожалуйста", "потом", "потому", "правильно", "сейчас", "сделай",
    "сделали", "смотри", "снова", "теперь", "тоже", "только", "тут", "уже",
    "хорошо", "было", "быть", "этого", "этот", "этой", "этом",
}

PATH_NOISE = {
    "applications", "application", "assistant", "claude", "codex", "current",
    "desktop", "downloads", "new", "root", "tmp", "users", "user", "volumes",
    "workspace", "workspaces", "repo", "repos", "project", "projects",
}

GENERIC_RELATION_TOKENS = {
    "final", "latest", "version", "release", "current", "new", "web", "site", "app",
    "product", "project", "work", "working", "folder", "workspace", "server", "local",
}


@dataclass
class ClusterRecord:
    raw_cluster: str
    canonical_cluster: str
    raw_members: set[str]
    summaries: list[Path]
    source_refs: list[str]
    ide_counts: Counter
    key_topics: set[str]
    path_tokens: set[str]
    content_tokens: set[str]
    raw_text: str

    @property
    def summary_count(self) -> int:
        return len(self.summaries)


def load_refresh_module():
    refresh_path = Path(__file__).resolve().parent / "refresh-memory.py"
    spec = importlib.util.spec_from_file_location("llm_wiki_refresh", refresh_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def load_registry() -> dict:
    if not REGISTRY_FILE.exists():
        return {"canonical_aliases": {}, "container_clusters": [], "candidate_families": []}
    return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))


def canonicalize(raw_cluster: str, alias_map: dict[str, str]) -> str:
    return alias_map.get(raw_cluster, raw_cluster)


def slug_title(slug: str) -> str:
    entity_path = ENTITY_DIR / f"{slug}.md"
    if entity_path.exists():
        for line in entity_path.read_text(encoding="utf-8").splitlines():
            if line.startswith('title: "'):
                return line.split('"', 1)[1].rsplit('"', 1)[0]
    return slug.replace("-", " ").replace("_", " ").title()


def tokenize_text(text: str, *, latin_only: bool = False) -> set[str]:
    regex = LATIN_RE if latin_only else WORD_RE
    tokens = set()
    for token in regex.findall(text.lower()):
        cleaned = token.strip("-_")
        if (
            len(cleaned) < 3
            or cleaned in STOPWORDS
            or cleaned in PATH_NOISE
            or re.fullmatch(r"[0-9]+", cleaned)
            or re.fullmatch(r"[0-9a-f]{6,}", cleaned)
        ):
            continue
        tokens.add(cleaned)
    return tokens


def parse_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = defaultdict(list)
    current = "_root"
    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip().lower()
            continue
        sections[current].append(line)
    return sections


def extract_quoted_block(lines: list[str]) -> str:
    block = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith(">"):
            block.append(stripped[1:].lstrip())
        elif block and not stripped:
            block.append("")
        elif block:
            break
    return "\n".join(block).strip()


def extract_key_topics(lines: list[str]) -> set[str]:
    topics = set()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            topic = stripped[2:].strip().lower()
            if topic and topic not in STOPWORDS:
                topics.add(topic)
    return topics


def extract_cwd_tokens(text: str) -> set[str]:
    match = re.search(r"<cwd>(.*?)</cwd>", text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return set()
    cwd = match.group(1)
    segments = re.split(r"[\\/ _-]+", cwd.lower())
    tokens = set()
    for segment in segments:
        cleaned = segment.strip()
        if (
            len(cleaned) < 3
            or cleaned in STOPWORDS
            or cleaned in PATH_NOISE
            or re.fullmatch(r"[0-9]+", cleaned)
            or re.fullmatch(r"[0-9a-f]{6,}", cleaned)
        ):
            continue
        tokens.add(cleaned)
    return tokens


def build_cluster_records(alias_map: dict[str, str]) -> dict[str, ClusterRecord]:
    grouped: dict[str, ClusterRecord] = {}

    for summary_path in sorted(SUMMARY_DIR.glob("chat-*.md")):
        match = FILENAME_RE.match(summary_path.name)
        if not match:
            continue

        raw_cluster = match.group(1)
        canonical_cluster = canonicalize(raw_cluster, alias_map)
        text = summary_path.read_text(encoding="utf-8")
        sections = parse_sections(text)

        ide_match = re.search(r"\*\*IDE:\*\*\s+([^\n]+)", text)
        ide = ide_match.group(1).strip() if ide_match else "unknown"
        key_topics = extract_key_topics(sections.get("key topics", []))
        initial_request = extract_quoted_block(sections.get("initial request", []))
        latest_prompt = extract_quoted_block(sections.get("latest user prompt", []))
        cwd_tokens = extract_cwd_tokens(initial_request)
        content_tokens = tokenize_text(f"{initial_request}\n{latest_prompt}", latin_only=True)

        source_refs = []
        for line in text.splitlines():
            if line.startswith("sources: ["):
                source_refs = re.findall(r'"([^"]+)"', line)
                break

        record = grouped.get(canonical_cluster)
        if record is None:
            record = ClusterRecord(
                raw_cluster=canonical_cluster,
                canonical_cluster=canonical_cluster,
                raw_members=set(),
                summaries=[],
                source_refs=[],
                ide_counts=Counter(),
                key_topics=set(),
                path_tokens=set(),
                content_tokens=set(),
                raw_text="",
            )
            grouped[canonical_cluster] = record

        record.summaries.append(summary_path)
        record.raw_members.add(raw_cluster)
        record.source_refs.extend(source_refs)
        record.ide_counts[ide] += 1
        record.key_topics.update(tokenize_text(" ".join(key_topics)))
        record.path_tokens.update(cwd_tokens)
        record.content_tokens.update(content_tokens)
        record.raw_text += "\n" + text.lower()

    return grouped


def token_frequencies(records: dict[str, ClusterRecord], attr: str) -> Counter:
    frequency = Counter()
    for record in records.values():
        frequency.update(getattr(record, attr))
    return frequency


def filtered_shared_tokens(left: set[str], right: set[str], frequency: Counter, max_df: int) -> list[str]:
    return sorted(token for token in (left & right) if frequency.get(token, 0) <= max_df and token not in GENERIC_RELATION_TOKENS)


def score_pair(
    a: ClusterRecord,
    b: ClusterRecord,
    *,
    path_frequency: Counter,
    topic_frequency: Counter,
    content_frequency: Counter,
) -> tuple[int, list[str]]:
    score = 0
    evidence = []
    categories = 0

    name_a = tokenize_text(a.raw_cluster.replace("-", " "), latin_only=False) - GENERIC_RELATION_TOKENS
    name_b = tokenize_text(b.raw_cluster.replace("-", " "), latin_only=False) - GENERIC_RELATION_TOKENS
    shared_name = sorted(name_a & name_b)
    if shared_name:
        score += min(6, 3 * len(shared_name))
        evidence.append(f"shared cluster tokens: {', '.join(shared_name[:4])}")
        categories += 1

    prefix = re.sub(r"[^a-z0-9]+", "", a.raw_cluster.lower())
    other_prefix = re.sub(r"[^a-z0-9]+", "", b.raw_cluster.lower())
    shared_prefix = ""
    for idx, (left, right) in enumerate(zip(prefix, other_prefix), start=1):
        if left != right:
            break
        shared_prefix = prefix[:idx]
    if len(shared_prefix) >= 6 and shared_prefix not in GENERIC_RELATION_TOKENS:
        score += 3
        evidence.append(f"name-prefix overlap: {shared_prefix}")
        categories += 1

    shared_paths = filtered_shared_tokens(a.path_tokens, b.path_tokens, path_frequency, max_df=2)
    if shared_paths:
        score += min(6, 2 * len(shared_paths))
        evidence.append(f"shared cwd tokens: {', '.join(shared_paths[:4])}")
        categories += 1

    shared_topics = filtered_shared_tokens(a.key_topics, b.key_topics, topic_frequency, max_df=2)
    if shared_topics:
        score += min(4, 2 * len(shared_topics))
        evidence.append(f"shared key topics: {', '.join(shared_topics[:4])}")
        categories += 1

    shared_content = filtered_shared_tokens(a.content_tokens, b.content_tokens, content_frequency, max_df=2)
    if shared_content:
        score += min(3, len(shared_content))
        evidence.append(f"shared prompt tokens: {', '.join(shared_content[:5])}")
        categories += 1

    member_mentions = []
    if any(member in b.raw_text for member in a.raw_members):
        member_mentions.append(a.raw_cluster)
    if any(member in a.raw_text for member in b.raw_members):
        member_mentions.append(b.raw_cluster)
    if member_mentions:
        score += 4
        evidence.append(f"explicit family reference: {', '.join(sorted(set(member_mentions)))}")
        categories += 1

    if categories < 2:
        return 0, []

    return score, evidence


def candidate_pairs(records: dict[str, ClusterRecord], container_clusters: set[str]) -> list[dict]:
    names = sorted(records)
    path_frequency = token_frequencies(records, "path_tokens")
    topic_frequency = token_frequencies(records, "key_topics")
    content_frequency = token_frequencies(records, "content_tokens")
    candidates = []
    for index, left_name in enumerate(names):
        for right_name in names[index + 1:]:
            if left_name in container_clusters or right_name in container_clusters:
                continue
            left = records[left_name]
            right = records[right_name]
            score, evidence = score_pair(
                left,
                right,
                path_frequency=path_frequency,
                topic_frequency=topic_frequency,
                content_frequency=content_frequency,
            )
            if score < 6:
                continue
            confidence = "high" if score >= 10 else "medium"
            candidates.append(
                {
                    "left": left_name,
                    "right": right_name,
                    "score": score,
                    "confidence": confidence,
                    "evidence": evidence,
                    "sources": sorted(set(left.source_refs[:2] + right.source_refs[:2])),
                }
            )
    return sorted(candidates, key=lambda item: (-item["score"], item["left"], item["right"]))


def format_ide_breakdown(counter: Counter) -> str:
    parts = [f"{ide} {count}" for ide, count in sorted(counter.items())]
    return ", ".join(parts) if parts else "unknown"


def build_query_page(records: dict[str, ClusterRecord], registry: dict, candidates: list[dict], today: str) -> str:
    candidate_families = registry.get("candidate_families", [])
    container_clusters = registry.get("container_clusters", [])
    canonical_families = sorted(records.values(), key=lambda item: (-item.summary_count, item.raw_cluster))

    sources = []
    for candidate in candidates[:6]:
        sources.extend(candidate["sources"])
    if not sources:
        for record in canonical_families[:6]:
            sources.extend(record.source_refs[:1])
    sources = sorted(dict.fromkeys(sources))[:12]

    lines = [
        "---",
        f'title: "Product Family Candidates — {today}"',
        "type: query",
        f"created: {today}",
        f"updated: {today}",
        "sources: [" + ", ".join(f'\"{source}\"' for source in sources) + "]",
        "tags: [analysis, normalization, product-families, identity, chat-history]",
        "status: active",
        "---",
        "",
        f"# Product Family Candidates — {today}",
        "",
        "This page records the current product-identity registry and the next candidate merges suggested by the heuristic scoring pass.",
        "",
        "## Registry Backed Canonical Families",
        "",
    ]

    for record in canonical_families[:16]:
        title = slug_title(record.raw_cluster)
        raw_members = sorted(
            {
                FILENAME_RE.match(path.name).group(1)
                for path in record.summaries
                if FILENAME_RE.match(path.name)
            }
        )
        lines.append(
            f"- `{title}` — `{record.summary_count}` summaries across `{', '.join(raw_members)}` "
            f"({format_ide_breakdown(record.ide_counts)})"
        )

    lines.extend([
        "",
        "## Candidate Families Already Tracked Manually",
        "",
    ])

    if candidate_families:
        for family in candidate_families:
            members = ", ".join(f"`{member}`" for member in family.get("members", []))
            lines.append(
                f"- `{family.get('canonical', 'unknown')}` candidate — members: {members}; "
                f"confidence `{family.get('confidence', 'unknown')}`; {family.get('notes', '').strip()}"
            )
    else:
        lines.append("- None yet.")

    lines.extend([
        "",
        "## Heuristic Candidate Merges",
        "",
        "These are not hard merges. They are review candidates suggested by overlap in summary text, key topics, path signals, or explicit cross-references.",
        "",
    ])

    if candidates:
        for candidate in candidates[:10]:
            left_title = slug_title(candidate["left"])
            right_title = slug_title(candidate["right"])
            evidence_text = "; ".join(candidate["evidence"][:3]) if candidate["evidence"] else "no specific evidence captured"
            lines.append(
                f"- `{left_title}` <-> `{right_title}` — score `{candidate['score']}` (`{candidate['confidence']}` confidence)"
            )
            lines.append(f"  Evidence: {evidence_text}.")
    else:
        lines.append("- No new candidates crossed the current score threshold.")

    lines.extend([
        "",
        "## Buckets To Keep Separate For Now",
        "",
    ])
    for bucket in container_clusters:
        lines.append(f"- `{bucket}`")

    lines.extend([
        "",
        "## Method",
        "",
        "- Use the alias registry first for accepted canonical merges.",
        "- Aggregate signals across each canonical family rather than trusting one chat name or one workspace path.",
        "- Score possible family overlaps using explicit references, path tokens, key topics, and prompt vocabulary.",
        "- Treat the output as review guidance, not as an automatic merge instruction.",
    ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Analyze likely product families across chat summaries")
    parser.add_argument("--dry-run", action="store_true", help="Print results without writing the wiki page")
    args = parser.parse_args()

    today = datetime.now().strftime("%Y-%m-%d")
    registry = load_registry()
    alias_map = registry.get("canonical_aliases", {})
    container_clusters = set(registry.get("container_clusters", []))
    records = build_cluster_records(alias_map)
    candidates = candidate_pairs(records, container_clusters)
    page_text = build_query_page(records, registry, candidates, today)

    if args.dry_run:
        print(page_text)
        return

    output_path = QUERY_DIR / f"product-family-candidates-{today}.md"
    output_path.write_text(page_text + "\n", encoding="utf-8")

    refresh = load_refresh_module()
    stats = refresh.rebuild_index()
    detail_lines = [
        "Ran the product-family scoring pass with the shared alias registry and filed the candidate merge report.",
        f"Pages touched: [[queries/product-family-candidates-{today}]]",
        f"Current strongest candidates recorded: {', '.join(f'`{item['left']}` <-> `{item['right']}`' for item in candidates[:3]) if candidates else 'none above threshold'}",
        f"Rebuilt index.md with {stats['total_pages']} total wiki pages.",
    ]
    refresh.insert_log_entry("QUERY | Product family candidates", "\n".join(detail_lines))
    print(f"Wrote {output_path}")
    print(f"Recorded {len(candidates)} candidate pair(s)")


if __name__ == "__main__":
    main()
