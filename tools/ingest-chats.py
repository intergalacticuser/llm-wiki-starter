#!/usr/bin/env python3
"""
LLM Wiki — Chat History Ingestion Tool

Extracts conversations from IDE chat histories and converts them into
structured markdown files for the LLM Wiki.

Supported IDEs:
  - Codex Desktop (~/.Codex/sessions/)
  - Claude Code (~/.claude/projects/)
  - Cursor (~/Library/Application Support/Cursor/  or  ~/.cursor/)
  - Windsurf (~/.windsurf/ or ~/Library/Application Support/Windsurf/)
  - Cline (VS Code extension storage)
  - Continue (~/.continue/)

Usage:
  python3 ingest-chats.py --help
  python3 ingest-chats.py --list                    # List all available projects/chats
  python3 ingest-chats.py --all                     # Ingest all chats from all IDEs
  python3 ingest-chats.py --project NAME            # Ingest all chats from a specific project
  python3 ingest-chats.py --chat PATH               # Ingest a specific chat file
  python3 ingest-chats.py --current                 # Ingest current project's chats
  python3 ingest-chats.py --ide codex               # Ingest from specific IDE only
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Optional

# ── Configuration ──────────────────────────────────────────────────────

WIKI_ROOT = Path(__file__).resolve().parent.parent
SOURCES_DIR = WIKI_ROOT / "sources" / "chats"
WIKI_DIR = WIKI_ROOT / "wiki"
SUMMARIES_DIR = WIKI_DIR / "summaries"
ENTITIES_DIR = WIKI_DIR / "entities"
CONCEPTS_DIR = WIKI_DIR / "concepts"
INDEX_FILE = WIKI_ROOT / "index.md"
LOG_FILE = WIKI_ROOT / "log.md"

# IDE chat storage locations
HOME = Path.home()

IDE_PATHS = {
    "codex": {
        "paths": [
            HOME / ".Codex" / "sessions",
            HOME / ".codex" / "sessions",
        ],
        "archived": [
            HOME / ".Codex" / "archived_sessions",
            HOME / ".codex" / "archived_sessions",
        ],
        "format": "jsonl",
    },
    "claude-code": {
        "projects": HOME / ".claude" / "projects",
        "sessions": HOME / ".claude" / "sessions",
        "format": "jsonl",
    },
    "cursor": {
        "paths": [
            HOME / "Library" / "Application Support" / "Cursor" / "User" / "workspaceStorage",
            HOME / ".config" / "Cursor" / "User" / "workspaceStorage",  # Linux
            HOME / ".cursor",
        ],
        "format": "vscdb",
    },
    "windsurf": {
        "paths": [
            HOME / "Library" / "Application Support" / "Windsurf" / "User" / "workspaceStorage",
            HOME / ".windsurf",
        ],
        "format": "vscdb",
    },
    "continue": {
        "paths": [
            HOME / ".continue" / "sessions",
        ],
        "format": "json",
    },
    "cline": {
        "paths": [
            HOME / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev",
            HOME / ".config" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev",
        ],
        "format": "json",
    },
}

NOISE_PREFIXES = (
    "# AGENTS.md instructions for ",
    "Base directory for this skill:",
    "/remote-control is active.",
)

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "there",
    "what", "when", "where", "have", "will", "just", "about", "your", "they",
    "them", "their", "then", "than", "were", "been", "being", "also", "after",
    "before", "because", "while", "would", "could", "should", "need", "want",
    "here", "like", "look", "using", "used", "over", "under", "much", "many",
    "more", "most", "some", "such", "only", "very", "into", "between",
    "если", "когда", "чтобы", "который", "которая", "которые", "потом",
    "сейчас", "нужно", "надо", "здесь", "теперь", "просто", "потому",
    "тогда", "после", "перед", "между", "этот", "эта", "эти", "того",
    "того", "того", "как", "что", "это", "для", "или", "она", "они",
    "оно", "его", "ее", "их", "мы", "вы", "ты", "там", "тут", "вот",
    "ещё", "еще", "уже", "где", "какой", "какая", "какие", "каким",
    "очень", "над", "под", "при", "без", "про", "нам", "вам", "мне",
}


# ── Message Extraction ─────────────────────────────────────────────────

def compact_whitespace(text: str) -> str:
    """Normalize whitespace without destroying paragraph structure."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def project_name_from_cwd(cwd: Optional[str], fallback: str = "") -> str:
    """Build a readable project name from a workspace path."""
    if cwd:
        name = Path(cwd).name.strip()
        if name:
            return name
    return fallback or "unknown-project"


def extract_text_from_content(content):
    """Extract plain text from various structured message content formats."""
    if isinstance(content, str):
        return compact_whitespace(content)
    if isinstance(content, dict):
        if "text" in content and isinstance(content["text"], str):
            return compact_whitespace(content["text"])
        return ""
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                item_type = item.get("type")
                if item_type in ("text", "input_text", "output_text"):
                    parts.append(item.get("text", ""))
            elif isinstance(item, str):
                parts.append(item)
        return compact_whitespace("\n".join(part for part in parts if part))
    return str(content)


def extract_command_args(text: str) -> str:
    """Extract the useful part from slash-command wrappers stored in chat logs."""
    match = re.search(r"<command-args>\s*(.*?)\s*</command-args>", text, re.DOTALL)
    if match:
        return compact_whitespace(match.group(1))
    return text


def normalize_user_text(text: str) -> str:
    """Remove IDE scaffolding and keep the user's actual request."""
    if not text:
        return ""

    text = compact_whitespace(text)

    if any(text.startswith(prefix) for prefix in NOISE_PREFIXES):
        return ""
    if text.startswith("<system-reminder>"):
        return ""

    if "<command-args>" in text:
        text = extract_command_args(text)
    elif text.startswith("<command-message>"):
        return ""

    return compact_whitespace(text)


def normalize_assistant_text(text: str) -> str:
    """Keep only visible assistant text, not tool scaffolding."""
    if not text:
        return ""
    text = compact_whitespace(text)
    if not text or text in ("[Tool result]", "[Tool: unknown]"):
        return ""
    return text


def should_keep_token(token: str) -> bool:
    """Simple filter for topic extraction."""
    if len(token) < 4:
        return False
    return token not in STOPWORDS


def infer_ide_from_path(filepath: Path) -> str:
    """Best-effort IDE inference for --chat mode."""
    path_text = str(filepath)
    if ".Codex" in path_text or ".codex" in path_text:
        return "codex"
    if ".claude" in path_text:
        return "claude-code"
    if "Cursor" in path_text or ".cursor" in path_text:
        return "cursor"
    if "Windsurf" in path_text or ".windsurf" in path_text:
        return "windsurf"
    if ".continue" in path_text:
        return "continue"
    return "claude-code"


def normalized_path_key(path: Path) -> str:
    """Normalize filesystem paths for deduping on case-insensitive volumes."""
    return str(path.expanduser().resolve()).lower()


def matches_project_filter(chat: dict, project_filter: Optional[str]) -> bool:
    """Match project filters against project names, cwd, and source paths."""
    if not project_filter:
        return True
    needle = project_filter.lower()
    haystacks = [
        chat.get("project", ""),
        chat.get("cwd", ""),
        str(chat.get("path", "")),
    ]
    return any(needle in str(value).lower() for value in haystacks if value)


def append_or_replace_message(messages, index_by_key, key, message):
    """Replace streamed duplicates when we have a stable message id."""
    if key and key in index_by_key:
        messages[index_by_key[key]] = message
        return
    if key:
        index_by_key[key] = len(messages)
    messages.append(message)


def parse_codex_jsonl(filepath: Path) -> dict:
    """Parse a Codex Desktop session JSONL file."""
    messages = []
    message_index = {}
    session_id = filepath.stem
    cwd = None
    started_at = None

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            obj_type = obj.get("type")
            payload = obj.get("payload", {})

            if obj_type == "session_meta":
                session_id = payload.get("id", session_id)
                cwd = payload.get("cwd", cwd)
                started_at = payload.get("timestamp", started_at)
                continue

            if obj_type != "response_item":
                continue

            if payload.get("type") != "message":
                continue

            role = payload.get("role")
            if role not in ("user", "assistant"):
                continue

            text = extract_text_from_content(payload.get("content", []))
            text = normalize_user_text(text) if role == "user" else normalize_assistant_text(text)
            if not text:
                continue

            message_key = None
            if role == "assistant":
                message_key = payload.get("id")

            append_or_replace_message(
                messages,
                message_index,
                message_key,
                {
                    "role": role,
                    "text": text,
                    "timestamp": obj.get("timestamp", ""),
                    "phase": payload.get("phase", ""),
                },
            )

    project = project_name_from_cwd(cwd, fallback=filepath.stem)

    return {
        "session_id": session_id,
        "project": project,
        "cwd": cwd,
        "messages": messages,
        "source_file": str(filepath),
        "ide": "codex",
        "started_at": started_at,
    }


def parse_claude_code_jsonl(filepath: Path) -> dict:
    """Parse a Claude Code JSONL conversation file."""
    messages = []
    message_index = {}
    session_id = None
    cwd = None
    started_at = None

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = obj.get("type", "")

            # Extract session metadata
            if msg_type == "queue-operation":
                if not session_id:
                    session_id = obj.get("sessionId")
                continue
            if not session_id:
                session_id = obj.get("sessionId", session_id)
            if not cwd:
                cwd = obj.get("cwd", cwd)

            # Extract messages
            if msg_type in ("user", "assistant"):
                message = obj.get("message", {})
                role = message.get("role", msg_type)
                content = message.get("content", "")
                text = extract_text_from_content(content)
                text = normalize_user_text(text) if role == "user" else normalize_assistant_text(text)

                if not text:
                    continue

                message_key = None
                if role == "assistant":
                    message_key = message.get("id") or obj.get("uuid")

                append_or_replace_message(
                    messages,
                    message_index,
                    message_key,
                    {
                        "role": role,
                        "text": text,
                        "timestamp": obj.get("timestamp", ""),
                    },
                )

    # Derive project name from filepath
    project_dir = filepath.parent.name
    if project_dir == "subagents":
        project_dir = filepath.parent.parent.parent.name

    project_name = project_name_from_cwd(cwd, fallback=project_dir.replace("-", " ").strip())

    return {
        "session_id": session_id or filepath.stem,
        "project": project_name,
        "cwd": cwd,
        "project_dir": project_dir,
        "messages": messages,
        "source_file": str(filepath),
        "ide": "claude-code",
    }


def parse_cursor_vscdb(filepath: Path) -> list:
    """Parse Cursor's SQLite workspace storage for chat history."""
    conversations = []
    try:
        conn = sqlite3.connect(str(filepath))
        cursor = conn.cursor()

        # Cursor stores chat data in ItemTable with specific keys
        cursor.execute("SELECT key, value FROM ItemTable WHERE key LIKE '%chat%' OR key LIKE '%conversation%' OR key LIKE '%aiChat%'")
        rows = cursor.fetchall()

        for key, value in rows:
            try:
                data = json.loads(value)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "messages" in item:
                            messages = []
                            for msg in item["messages"]:
                                if isinstance(msg, dict):
                                    messages.append({
                                        "role": msg.get("role", "unknown"),
                                        "text": extract_text_from_content(msg.get("content", "")),
                                        "timestamp": msg.get("timestamp", ""),
                                    })
                            if messages:
                                conversations.append({
                                    "session_id": item.get("id", key),
                                    "project": "cursor-workspace",
                                    "messages": messages,
                                    "source_file": str(filepath),
                                    "ide": "cursor",
                                })
                elif isinstance(data, dict) and "messages" in data:
                    messages = []
                    for msg in data["messages"]:
                        if isinstance(msg, dict):
                            messages.append({
                                "role": msg.get("role", "unknown"),
                                "text": extract_text_from_content(msg.get("content", "")),
                                "timestamp": msg.get("timestamp", ""),
                            })
                    if messages:
                        conversations.append({
                            "session_id": data.get("id", key),
                            "project": "cursor-workspace",
                            "messages": messages,
                            "source_file": str(filepath),
                            "ide": "cursor",
                        })
            except (json.JSONDecodeError, TypeError):
                continue

        conn.close()
    except (sqlite3.Error, Exception) as e:
        print(f"  Warning: Could not read {filepath}: {e}", file=sys.stderr)

    return conversations


def parse_continue_json(filepath: Path) -> dict:
    """Parse Continue session JSON files."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)

        messages = []
        history = data.get("history", data.get("messages", []))
        for msg in history:
            if isinstance(msg, dict):
                messages.append({
                    "role": msg.get("role", "unknown"),
                    "text": extract_text_from_content(msg.get("content", "")),
                    "timestamp": msg.get("timestamp", ""),
                })

        return {
            "session_id": data.get("sessionId", filepath.stem),
            "project": data.get("workspaceDirectory", "continue-session"),
            "messages": messages,
            "source_file": str(filepath),
            "ide": "continue",
        }
    except (json.JSONDecodeError, Exception) as e:
        print(f"  Warning: Could not read {filepath}: {e}", file=sys.stderr)
        return None


# ── Discovery ──────────────────────────────────────────────────────────

def discover_claude_code_chats(project_filter: Optional[str] = None) -> list:
    """Find all Claude Code conversation files."""
    chats = []
    projects_dir = IDE_PATHS["claude-code"]["projects"]
    if not projects_dir.exists():
        return chats

    for project_dir in sorted(projects_dir.iterdir()):
        if not project_dir.is_dir():
            continue
        if project_filter and project_filter not in project_dir.name:
            continue

        # Find JSONL files (skip subagent files)
        for jsonl_file in project_dir.glob("*.jsonl"):
            info = {
                "path": jsonl_file,
                "project": project_dir.name,
                "size": jsonl_file.stat().st_size,
                "modified": datetime.fromtimestamp(jsonl_file.stat().st_mtime),
                "ide": "claude-code",
            }
            if matches_project_filter(info, project_filter):
                chats.append(info)

    return chats


def discover_codex_chats(project_filter: Optional[str] = None, include_archived: bool = False) -> list:
    """Find all Codex Desktop session files."""
    chats = []
    seen_files = set()
    scan_roots = list(IDE_PATHS["codex"]["paths"])
    if include_archived:
        scan_roots.extend(IDE_PATHS["codex"]["archived"])

    for root in scan_roots:
        if not root.exists():
            continue
        for jsonl_file in root.rglob("*.jsonl"):
            if not jsonl_file.is_file():
                continue
            file_key = normalized_path_key(jsonl_file)
            if file_key in seen_files:
                continue
            seen_files.add(file_key)
            info = {
                "path": jsonl_file,
                "project": jsonl_file.stem,
                "size": jsonl_file.stat().st_size,
                "modified": datetime.fromtimestamp(jsonl_file.stat().st_mtime),
                "ide": "codex",
            }
            if matches_project_filter(info, project_filter):
                chats.append(info)

    return chats


def discover_all_chats(ide_filter: Optional[str] = None, project_filter: Optional[str] = None) -> list:
    """Discover all available chat files across IDEs."""
    all_chats = []

    if not ide_filter or ide_filter == "codex":
        all_chats.extend(discover_codex_chats(project_filter))

    if not ide_filter or ide_filter == "claude-code":
        all_chats.extend(discover_claude_code_chats(project_filter))

    if not ide_filter or ide_filter == "cursor":
        for p in IDE_PATHS["cursor"]["paths"]:
            if p.exists():
                for vscdb in p.rglob("state.vscdb"):
                    all_chats.append({
                        "path": vscdb,
                        "project": vscdb.parent.name,
                        "size": vscdb.stat().st_size,
                        "modified": datetime.fromtimestamp(vscdb.stat().st_mtime),
                        "ide": "cursor",
                    })

    if not ide_filter or ide_filter == "continue":
        for p in IDE_PATHS["continue"]["paths"]:
            if p.exists():
                for jf in p.glob("*.json"):
                    all_chats.append({
                        "path": jf,
                        "project": "continue",
                        "size": jf.stat().st_size,
                        "modified": datetime.fromtimestamp(jf.stat().st_mtime),
                        "ide": "continue",
                    })

    if not ide_filter or ide_filter == "windsurf":
        for p in IDE_PATHS["windsurf"]["paths"]:
            if p.exists():
                for vscdb in p.rglob("state.vscdb"):
                    all_chats.append({
                        "path": vscdb,
                        "project": vscdb.parent.name,
                        "size": vscdb.stat().st_size,
                        "modified": datetime.fromtimestamp(vscdb.stat().st_mtime),
                        "ide": "windsurf",
                    })

    filtered = [chat for chat in all_chats if matches_project_filter(chat, project_filter)]
    return sorted(filtered, key=lambda x: x["modified"], reverse=True)


# ── Conversation Processing ────────────────────────────────────────────

def conversation_to_markdown(conv: dict) -> str:
    """Convert a parsed conversation to a readable markdown document."""
    lines = []
    lines.append(f"---")
    lines.append(f'title: "Chat: {conv["project"]}"')
    lines.append(f"type: summary")
    lines.append(f"created: {datetime.now().strftime('%Y-%m-%d')}")
    lines.append(f"updated: {datetime.now().strftime('%Y-%m-%d')}")
    lines.append(f'sources: ["{conv.get("source_file", "unknown")}"]')
    lines.append(f'tags: [chat, {conv["ide"]}]')
    lines.append(f"status: active")
    lines.append(f"---")
    lines.append("")
    lines.append(f"# Chat: {conv['project']}")
    lines.append("")
    lines.append(f"**IDE:** {conv['ide']}")
    lines.append(f"**Session:** {conv['session_id']}")
    lines.append(f"**Messages:** {len(conv['messages'])}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for msg in conv["messages"]:
        role = msg["role"].upper()
        text = msg["text"]

        lines.append(f"### {role}")
        lines.append("")
        lines.append(text)
        lines.append("")

    return "\n".join(lines)


def extract_key_info(conv: dict) -> dict:
    """Extract key decisions, topics, entities from a conversation."""
    token_counter = Counter()
    user_messages = []
    assistant_messages = []

    for msg in conv["messages"]:
        text = msg["text"]
        if msg["role"] == "user":
            user_messages.append(text)
            tokens = re.findall(r"[A-Za-zА-Яа-я0-9][A-Za-zА-Яа-я0-9_-]+", text.lower())
            token_counter.update(token for token in tokens if should_keep_token(token))
        elif msg["role"] == "assistant":
            if text:
                assistant_messages.append(text)

    return {
        "topics": [token for token, _ in token_counter.most_common(12)],
        "user_message_count": len(user_messages),
        "assistant_message_count": len(assistant_messages),
        "first_user_message": user_messages[0] if user_messages else "",
        "last_user_message": user_messages[-1] if user_messages else "",
        "last_assistant_message": assistant_messages[-1] if assistant_messages else "",
    }


def generate_chat_summary(conv: dict, key_info: dict) -> str:
    """Generate a concise summary page for a chat conversation."""
    today = datetime.now().strftime("%Y-%m-%d")
    project = conv["project"]
    session = conv["session_id"][:8]

    lines = []
    lines.append("---")
    lines.append(f'title: "Chat Summary: {project} ({session})"')
    lines.append(f"type: summary")
    lines.append(f"created: {today}")
    lines.append(f"updated: {today}")
    lines.append(f'sources: ["chats/{safe_filename(project)}_{session}.md"]')
    lines.append(f"tags: [chat-summary, {conv['ide']}]")
    lines.append(f"status: active")
    lines.append("---")
    lines.append("")
    lines.append(f"# Chat Summary: {project}")
    lines.append("")
    lines.append(f"**IDE:** {conv['ide']}  ")
    lines.append(f"**Session:** `{conv['session_id']}`  ")
    lines.append(f"**Messages:** {len(conv['messages'])} ({key_info['user_message_count']} user, {key_info['assistant_message_count']} assistant)  ")
    lines.append(f"**Processed:** {today}  ")
    lines.append("")

    if key_info["first_user_message"]:
        lines.append("## Initial Request")
        lines.append("")
        lines.append(f"> {key_info['first_user_message'][:700]}")
        lines.append("")

    if key_info["topics"]:
        lines.append("## Key Topics")
        lines.append("")
        for topic in key_info["topics"]:
            lines.append(f"- {topic}")
        lines.append("")

    if key_info["last_user_message"] and key_info["last_user_message"] != key_info["first_user_message"]:
        lines.append("## Latest User Prompt")
        lines.append("")
        lines.append(f"> {key_info['last_user_message'][:700]}")
        lines.append("")

    lines.append("## Full Transcript")
    lines.append("")
    lines.append(f"See [[chats/{safe_filename(project)}_{session}]] for the complete conversation.")
    lines.append("")

    return "\n".join(lines)


# ── File Operations ────────────────────────────────────────────────────

def safe_filename(name: str) -> str:
    """Convert a string to a safe filename."""
    # Remove or replace problematic characters
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'[\s]+', '-', name)
    name = name.strip('-').lower()
    return name[:80] if name else "unnamed"


def save_chat(conv: dict, output_dir: Path = None) -> tuple:
    """Save a conversation as markdown files. Returns (raw_path, summary_path)."""
    if output_dir is None:
        output_dir = SOURCES_DIR

    output_dir.mkdir(parents=True, exist_ok=True)
    SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)

    project = safe_filename(conv["project"])
    session = conv["session_id"][:8]
    filename = f"{project}_{session}"

    # Save raw conversation transcript
    raw_path = output_dir / f"{filename}.md"
    raw_content = conversation_to_markdown(conv)
    raw_path.write_text(raw_content, encoding="utf-8")

    # Save summary
    key_info = extract_key_info(conv)
    summary_path = SUMMARIES_DIR / f"chat-{filename}.md"
    summary_content = generate_chat_summary(conv, key_info)
    summary_path.write_text(summary_content, encoding="utf-8")

    return raw_path, summary_path


def update_log(action: str, details: str):
    """Append an entry to the wiki log."""
    today = datetime.now().strftime("%Y-%m-%d")
    entry = f"\n## [{today}] {action}\n{details}\n"

    if LOG_FILE.exists():
        content = LOG_FILE.read_text(encoding="utf-8")
        # Insert after the header section (after the first ---)
        marker = "---\n\n"
        pos = content.rfind(marker)
        if pos != -1:
            insert_at = pos + len(marker)
            content = content[:insert_at] + entry + content[insert_at:]
        else:
            content += entry
        LOG_FILE.write_text(content, encoding="utf-8")


# ── Main Commands ──────────────────────────────────────────────────────

def cmd_list(args):
    """List all available chat files."""
    chats = discover_all_chats(ide_filter=args.ide)

    if not chats:
        print("No chat histories found.")
        return

    print(f"\n{'IDE':<15} {'Project':<45} {'Size':>10} {'Modified':<20}")
    print("-" * 95)

    for chat in chats:
        project = chat["project"]
        if len(project) > 43:
            project = "..." + project[-40:]
        size = f"{chat['size'] / 1024:.1f}KB"
        modified = chat["modified"].strftime("%Y-%m-%d %H:%M")
        print(f"{chat['ide']:<15} {project:<45} {size:>10} {modified:<20}")

    print(f"\nTotal: {len(chats)} chat files found")


def cmd_ingest(args):
    """Ingest chat files into the wiki."""
    # Determine which chats to process
    if args.chat:
        # Specific chat file
        filepath = Path(args.chat).resolve()
        if not filepath.exists():
            print(f"Error: File not found: {filepath}", file=sys.stderr)
            sys.exit(1)
        chats_to_process = [{"path": filepath, "ide": infer_ide_from_path(filepath), "project": filepath.parent.name}]
    elif args.current:
        # Current project only
        cwd = Path.cwd()
        chats_to_process = discover_all_chats(project_filter=str(cwd), ide_filter=args.ide)
    elif args.project:
        chats_to_process = discover_all_chats(project_filter=args.project, ide_filter=args.ide)
    elif args.all:
        chats_to_process = discover_all_chats(ide_filter=args.ide)
    else:
        print("Error: Specify --all, --current, --project NAME, or --chat PATH", file=sys.stderr)
        sys.exit(1)

    if not chats_to_process:
        print("No matching chats found.")
        return

    print(f"\nFound {len(chats_to_process)} chat file(s) to process...\n")

    processed = 0
    pages_created = 0
    all_summaries = []

    for chat_info in chats_to_process:
        filepath = chat_info["path"]
        ide = chat_info["ide"]

        print(f"  Processing: {filepath.name} ({ide})")

        try:
            if ide == "codex":
                conv = parse_codex_jsonl(filepath)
                if conv and conv["messages"]:
                    raw_path, summary_path = save_chat(conv)
                    print(f"    -> {raw_path.name}")
                    print(f"    -> {summary_path.name}")
                    processed += 1
                    pages_created += 2
                    all_summaries.append(summary_path.stem)
                else:
                    print(f"    (skipped: no messages)")

            elif ide == "claude-code":
                conv = parse_claude_code_jsonl(filepath)
                if conv and conv["messages"]:
                    raw_path, summary_path = save_chat(conv)
                    print(f"    -> {raw_path.name}")
                    print(f"    -> {summary_path.name}")
                    processed += 1
                    pages_created += 2
                    all_summaries.append(summary_path.stem)
                else:
                    print(f"    (skipped: no messages)")

            elif ide in ("cursor", "windsurf"):
                conversations = parse_cursor_vscdb(filepath)
                for conv in conversations:
                    if conv and conv["messages"]:
                        raw_path, summary_path = save_chat(conv)
                        print(f"    -> {raw_path.name}")
                        processed += 1
                        pages_created += 2
                        all_summaries.append(summary_path.stem)

            elif ide == "continue":
                conv = parse_continue_json(filepath)
                if conv and conv["messages"]:
                    raw_path, summary_path = save_chat(conv)
                    print(f"    -> {raw_path.name}")
                    processed += 1
                    pages_created += 2
                    all_summaries.append(summary_path.stem)

        except Exception as e:
            print(f"    Error: {e}", file=sys.stderr)

    # Update log
    if processed > 0:
        details = (
            f"Ingested {processed} conversation(s) from IDE chat histories.\n"
            f"Pages created: {pages_created}\n"
            f"Summaries: {', '.join(f'[[summaries/{s}]]' for s in all_summaries[:10])}"
        )
        update_log("INGEST-CHATS | Chat history ingestion", details)

    print(f"\nDone! Processed {processed} conversations, created {pages_created} wiki pages.")
    print(f"Raw transcripts: sources/chats/")
    print(f"Summaries:       wiki/summaries/")


def cmd_ingest_for_llm(args):
    """
    Ingest mode designed to be called by an LLM inside a chat session.
    Outputs structured JSON for the LLM to process further.
    """
    if args.project:
        chats = discover_all_chats(project_filter=args.project)
    elif args.current:
        chats = discover_all_chats(project_filter=str(Path.cwd()))
    elif args.all:
        chats = discover_all_chats()
    else:
        chats = discover_all_chats()

    results = []
    for chat_info in chats[:args.limit if hasattr(args, 'limit') else 50]:
        filepath = chat_info["path"]
        ide = chat_info["ide"]

        try:
            if ide == "codex":
                conv = parse_codex_jsonl(filepath)
                if conv and conv["messages"]:
                    raw_path, summary_path = save_chat(conv)
                    results.append({
                        "project": conv["project"],
                        "session": conv["session_id"],
                        "messages": len(conv["messages"]),
                        "raw_file": str(raw_path),
                        "summary_file": str(summary_path),
                    })
            elif ide == "claude-code":
                conv = parse_claude_code_jsonl(filepath)
                if conv and conv["messages"]:
                    raw_path, summary_path = save_chat(conv)
                    results.append({
                        "project": conv["project"],
                        "session": conv["session_id"],
                        "messages": len(conv["messages"]),
                        "raw_file": str(raw_path),
                        "summary_file": str(summary_path),
                    })
        except Exception as e:
            results.append({"error": str(e), "file": str(filepath)})

    print(json.dumps({"processed": len(results), "results": results}, indent=2))


# ── CLI ────────────────────────────────────────────────────────────────

def main():
    ide_arg = {
        "type": str.lower,
        "choices": ["codex", "claude-code", "cursor", "windsurf", "continue", "cline"],
    }

    parser = argparse.ArgumentParser(
        description="LLM Wiki — Chat History Ingestion Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command")

    # list
    list_parser = subparsers.add_parser("list", help="List available chat files")
    list_parser.add_argument("--ide", **ide_arg)

    # ingest
    ingest_parser = subparsers.add_parser("ingest", help="Ingest chats into wiki")
    ingest_group = ingest_parser.add_mutually_exclusive_group(required=True)
    ingest_group.add_argument("--all", action="store_true", help="Ingest all chats from all IDEs")
    ingest_group.add_argument("--current", action="store_true", help="Ingest current project's chats")
    ingest_group.add_argument("--project", type=str, help="Ingest chats from a specific project")
    ingest_group.add_argument("--chat", type=str, help="Ingest a specific chat file")
    ingest_parser.add_argument("--ide", **ide_arg)

    # llm-ingest (for calling from LLM)
    llm_parser = subparsers.add_parser("llm-ingest", help="Ingest for LLM processing (JSON output)")
    llm_group = llm_parser.add_mutually_exclusive_group()
    llm_group.add_argument("--all", action="store_true")
    llm_group.add_argument("--current", action="store_true")
    llm_group.add_argument("--project", type=str)
    llm_parser.add_argument("--limit", type=int, default=50)

    # Backward compatibility: support --list, --all etc. as top-level args
    parser.add_argument("--list", action="store_true", help="List available chats")

    args = parser.parse_args()

    if args.list:
        args.ide = None
        cmd_list(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "ingest":
        cmd_ingest(args)
    elif args.command == "llm-ingest":
        cmd_ingest_for_llm(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
