"""Memory system for persistent agent memory."""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger

from nanobot.utils.helpers import ensure_dir

if TYPE_CHECKING:
    from nanobot.openviking.client import VikingClient
    from nanobot.providers.base import LLMProvider
    from nanobot.session.manager import Session

_DATE_PREFIX_RE = re.compile(r"^\[(\d{4}-\d{2}-\d{2})")

_SAVE_MEMORY_TOOL = [
    {
        "type": "function",
        "function": {
            "name": "save_memory",
            "description": "Save the memory consolidation result to persistent storage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "history_entry": {
                        "type": "string",
                        "description": "A paragraph (2-5 sentences) summarizing key events/decisions/topics. "
                        "Start with [YYYY-MM-DD HH:MM]. Include detail useful for grep search.",
                    },
                    "memory_update": {
                        "type": "string",
                        "description": "Full updated long-term memory as markdown. Include all existing "
                        "facts plus new ones. Return unchanged if nothing new.",
                    },
                },
                "required": ["history_entry", "memory_update"],
            },
        },
    }
]


class MemoryStore:
    """Two-layer memory: MEMORY.md (long-term facts) + daily history files (grep-searchable log)."""

    def __init__(self, workspace: Path):
        self.memory_dir = ensure_dir(workspace / "memory")
        self.memory_file = self.memory_dir / "MEMORY.md"
        self.history_dir = ensure_dir(self.memory_dir / "history")
        self._legacy_history_file = self.memory_dir / "HISTORY.md"

    # ------------------------------------------------------------------
    # Long-term memory (MEMORY.md) — unchanged
    # ------------------------------------------------------------------

    def read_long_term(self) -> str:
        if self.memory_file.exists():
            return self.memory_file.read_text(encoding="utf-8")
        return ""

    def write_long_term(self, content: str) -> None:
        self.memory_file.write_text(content, encoding="utf-8")

    def get_memory_context(self) -> str:
        long_term = self.read_long_term()
        return f"## Long-term Memory\n{long_term}" if long_term else ""

    # ------------------------------------------------------------------
    # Daily history files
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_date_from_entry(entry: str) -> str:
        """Extract YYYY-MM-DD from a ``[YYYY-MM-DD ...]`` prefix, fallback to today."""
        m = _DATE_PREFIX_RE.match(entry.strip())
        return m.group(1) if m else date.today().isoformat()

    def _daily_file(self, day: str) -> Path:
        return self.history_dir / f"{day}.md"

    def append_history(self, entry: str) -> None:
        """Append *entry* to the daily history file derived from its date prefix."""
        day = self._parse_date_from_entry(entry)
        with open(self._daily_file(day), "a", encoding="utf-8") as f:
            f.write(entry.rstrip() + "\n\n")

    def list_history_files(self) -> list[Path]:
        """Return ``history/*.md`` sorted by filename (i.e. date ascending)."""
        files = sorted(self.history_dir.glob("*.md"))
        return files

    def read_history(self, days: int | None = None) -> str:
        """Read concatenated history.  *days*=None means all files."""
        files = self.list_history_files()
        if days is not None and days > 0:
            cutoff = (date.today() - timedelta(days=days)).isoformat()
            files = [f for f in files if f.stem >= cutoff]
        parts: list[str] = []
        for f in files:
            parts.append(f.read_text(encoding="utf-8"))
        return "\n".join(parts)

    def search_history(self, pattern: str) -> list[tuple[str, str]]:
        """Grep *pattern* (case-insensitive) across all daily files.

        Returns list of ``(date_stem, matching_line)`` tuples.
        """
        try:
            compiled = re.compile(pattern, re.IGNORECASE)
        except re.error:
            compiled = re.compile(re.escape(pattern), re.IGNORECASE)

        results: list[tuple[str, str]] = []
        for f in self.list_history_files():
            for line in f.read_text(encoding="utf-8").splitlines():
                if compiled.search(line):
                    results.append((f.stem, line))
        return results

    def get_history_stats(self) -> dict[str, Any]:
        """Return stats: file count, total bytes, date range."""
        files = self.list_history_files()
        total_bytes = sum(f.stat().st_size for f in files)
        return {
            "file_count": len(files),
            "total_bytes": total_bytes,
            "earliest": files[0].stem if files else None,
            "latest": files[-1].stem if files else None,
        }

    def cleanup_history(self, retention_days: int) -> int:
        """Delete daily files older than *retention_days*.  Returns count deleted."""
        if retention_days <= 0:
            return 0
        cutoff = (date.today() - timedelta(days=retention_days)).isoformat()
        deleted = 0
        for f in self.list_history_files():
            if f.stem < cutoff:
                f.unlink()
                deleted += 1
        if deleted:
            logger.info("History cleanup: deleted {} files older than {}", deleted, cutoff)
        return deleted

    # ------------------------------------------------------------------
    # Legacy migration
    # ------------------------------------------------------------------

    def migrate_legacy_history(self) -> bool:
        """Split old single-file ``HISTORY.md`` into daily files.

        Returns True if migration was performed, False if skipped.
        """
        if not self._legacy_history_file.exists():
            return False
        content = self._legacy_history_file.read_text(encoding="utf-8").strip()
        if not content:
            self._legacy_history_file.rename(self._legacy_history_file.with_suffix(".md.bak"))
            return True

        buckets: dict[str, list[str]] = {}
        current_entry_lines: list[str] = []
        current_day: str | None = None

        for line in content.splitlines():
            m = _DATE_PREFIX_RE.match(line)
            if m:
                if current_entry_lines and current_day:
                    buckets.setdefault(current_day, []).append("\n".join(current_entry_lines))
                current_day = m.group(1)
                current_entry_lines = [line]
            else:
                current_entry_lines.append(line)

        if current_entry_lines and current_day:
            buckets.setdefault(current_day, []).append("\n".join(current_entry_lines))
        elif current_entry_lines and not current_day:
            today = date.today().isoformat()
            buckets.setdefault(today, []).append("\n".join(current_entry_lines))

        for day, entries in buckets.items():
            with open(self._daily_file(day), "a", encoding="utf-8") as f:
                for entry in entries:
                    f.write(entry.rstrip() + "\n\n")

        self._legacy_history_file.rename(self._legacy_history_file.with_suffix(".md.bak"))
        logger.info("Migrated legacy HISTORY.md into {} daily files", len(buckets))
        return True

    # ------------------------------------------------------------------
    # OpenViking semantic memory
    # ------------------------------------------------------------------

    async def get_viking_memory_context(
        self, current_message: str, viking_client: VikingClient,
    ) -> str:
        """Fetch relevant memories from OpenViking for the current message."""
        try:
            return await viking_client.get_viking_memory_context(current_message)
        except Exception as e:
            logger.warning("OpenViking memory context failed: {}", e)
            return ""

    async def get_viking_user_profile(self, viking_client: VikingClient) -> str:
        """Fetch user profile from OpenViking."""
        try:
            return await viking_client.get_viking_user_profile()
        except Exception as e:
            logger.warning("OpenViking user profile failed: {}", e)
            return ""

    async def consolidate(
        self,
        session: Session,
        provider: LLMProvider,
        model: str,
        *,
        archive_all: bool = False,
        memory_window: int = 50,
        history_retention_days: int = 0,
    ) -> bool:
        """Consolidate old messages into MEMORY.md + daily history files via LLM tool call.

        When *history_retention_days* > 0, old daily files are pruned after consolidation.
        Returns True on success (including no-op), False on failure.
        """
        if archive_all:
            old_messages = session.messages
            keep_count = 0
            logger.info("Memory consolidation (archive_all): {} messages", len(session.messages))
        else:
            keep_count = memory_window // 2
            if len(session.messages) <= keep_count:
                return True
            if len(session.messages) - session.last_consolidated <= 0:
                return True
            old_messages = session.messages[session.last_consolidated:-keep_count]
            if not old_messages:
                return True
            logger.info("Memory consolidation: {} to consolidate, {} keep", len(old_messages), keep_count)

        lines = []
        for m in old_messages:
            if not m.get("content"):
                continue
            tools = f" [tools: {', '.join(m['tools_used'])}]" if m.get("tools_used") else ""
            lines.append(f"[{m.get('timestamp', '?')[:16]}] {m['role'].upper()}{tools}: {m['content']}")

        current_memory = self.read_long_term()
        prompt = f"""Process this conversation and call the save_memory tool with your consolidation.

## Current Long-term Memory
{current_memory or "(empty)"}

## Conversation to Process
{chr(10).join(lines)}"""

        try:
            response = await provider.chat(
                messages=[
                    {"role": "system", "content": "You are a memory consolidation agent. Call the save_memory tool with your consolidation of the conversation."},
                    {"role": "user", "content": prompt},
                ],
                tools=_SAVE_MEMORY_TOOL,
                model=model,
            )

            if not response.has_tool_calls:
                logger.warning("Memory consolidation: LLM did not call save_memory, skipping")
                return False

            args = response.tool_calls[0].arguments
            # Some providers return arguments as a JSON string instead of dict
            if isinstance(args, str):
                args = json.loads(args)
            if not isinstance(args, dict):
                logger.warning("Memory consolidation: unexpected arguments type {}", type(args).__name__)
                return False

            if entry := args.get("history_entry"):
                if not isinstance(entry, str):
                    entry = json.dumps(entry, ensure_ascii=False)
                self.append_history(entry)
            if update := args.get("memory_update"):
                if not isinstance(update, str):
                    update = json.dumps(update, ensure_ascii=False)
                if update != current_memory:
                    self.write_long_term(update)

            session.last_consolidated = 0 if archive_all else len(session.messages) - keep_count
            logger.info("Memory consolidation done: {} messages, last_consolidated={}", len(session.messages), session.last_consolidated)

            if history_retention_days > 0:
                self.cleanup_history(history_retention_days)

            return True
        except Exception:
            logger.exception("Memory consolidation failed")
            return False
