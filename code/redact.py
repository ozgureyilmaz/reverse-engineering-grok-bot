"""Redaction helpers.

The transcripts in evidence/ were already redacted before publication.
This module replaces study codenames with public bot labels, replaces any
UUID-shaped string with [id], and replaces caller-supplied exact tokens.
It does not contain the removed personal values. Those are described, not
stored, in evidence/REDACTIONS.json.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from receipts import BOT_NAMES

_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", re.I)


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def redact_text(text: str, tokens: list[str] | None = None) -> tuple[str, dict[str, int]]:
    """Return redacted text and counts by kind.

    `tokens` are exact strings, longest first, replaced with [city]. Used for
    a caller-supplied name. The published evidence does not need this argument.
    """
    counts: dict[str, int] = {}
    out = text
    for token in sorted(tokens or [], key=len, reverse=True):
        if not token:
            continue
        n = out.count(token)
        if n:
            out = out.replace(token, "[city]")
            counts["operator_city"] = counts.get("operator_city", 0) + n
    id_n = len(_UUID.findall(out))
    if id_n:
        out = _UUID.sub("[id]", out)
        counts["bot_id"] = id_n
    name_n = 0
    for name in sorted(BOT_NAMES, key=len, reverse=True):
        pattern = re.compile(rf"\b{re.escape(name)}\b")
        found = pattern.findall(out)
        name_n += len(found)
        out = pattern.sub(BOT_NAMES[name], out)
    if name_n:
        counts["bot_name"] = name_n
    for label in sorted(set(BOT_NAMES.values()), key=len, reverse=True):
        out = out.replace(f"{label} ({label})", label)
    return out, counts


def public_name(src: Path) -> str:
    name = src.name
    name = name.replace("grs-np-tr__memory_check_after.md", "bot-tr-1__memory_check_after.md")
    name = name.replace("grs-pref-tr__memory_check_after.md", "bot-tr-pref__memory_check_after.md")
    name = name.replace("pref-setup-notes.md", "profile-setup-notes.md")
    if name.startswith("CHECKOUT-US"):
        return "CHECKOUT-US.md"
    if name.startswith("CHECKOUT-TR"):
        return "CHECKOUT-TR.md"
    return name
