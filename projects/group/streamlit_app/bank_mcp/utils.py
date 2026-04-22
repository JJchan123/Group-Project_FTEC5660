"""Helpers for the bank transfer review MCP.

This module keeps the bank transfer beneficiary checking logic simple,
deterministic, and safe for local demo use.
"""

from __future__ import annotations

import hashlib
import re
from difflib import SequenceMatcher

_PUNCT_RE = re.compile(r"[^A-Z0-9\s]")
_SPACE_RE = re.compile(r"\s+")
_SUFFIX_MAP = {
    "LIMITED": "LTD",
    "LTD.": "LTD",
    "COMPANY": "CO",
    "COMPANYS": "CO",
    "CORPORATION": "CORP",
}


def normalize_name(name: str | None) -> str:
    """Normalize beneficiary names for bank transfer review matching."""
    if not name:
        return ""

    upper = name.upper().strip()
    upper = _PUNCT_RE.sub(" ", upper)
    tokens = [_SUFFIX_MAP.get(token, token) for token in _SPACE_RE.split(upper) if token]
    return " ".join(tokens)


def hash_account_number(account_number: str) -> str:
    """Hash account numbers before SQLite storage or lookup."""
    canonical = canonicalize_account_number(account_number)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def mask_account_number(account_number: str) -> str:
    """Mask account numbers for safe logging and demo output."""
    canonical = canonicalize_account_number(account_number)
    if not canonical:
        return "****"
    return f"****{canonical[-4:]}"


def canonicalize_account_number(account_number: str | None) -> str:
    """Strip separators so the same account hashes consistently."""
    if not account_number:
        return ""
    return re.sub(r"[^A-Za-z0-9]", "", account_number).upper()


def classify_name_match(
    recipient_name: str,
    official_name: str,
    aliases: list[str],
) -> str:
    """Return match / close_match / mismatch for bank transfer review."""
    candidate = normalize_name(recipient_name)
    official = normalize_name(official_name)
    alias_norms = [normalize_name(alias) for alias in aliases if normalize_name(alias)]

    if not candidate or not official:
        return "unknown"
    if candidate == official:
        return "match"
    if candidate in alias_norms:
        return "close_match"
    if _is_near_match(candidate, official):
        return "close_match"
    if any(_is_near_match(candidate, alias) for alias in alias_norms):
        return "close_match"
    return "mismatch"


def _is_near_match(left: str, right: str) -> bool:
    if not left or not right:
        return False
    if left in right or right in left:
        return True

    left_tokens = set(left.split())
    right_tokens = set(right.split())
    if left_tokens and right_tokens:
        overlap = len(left_tokens & right_tokens) / max(len(left_tokens), len(right_tokens))
        if overlap >= 0.75:
            return True

    return SequenceMatcher(None, left, right).ratio() >= 0.88
