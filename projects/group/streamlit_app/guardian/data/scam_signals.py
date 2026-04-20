"""Scam-signal provider abstraction.

This module decouples *where* scam signals come from (local CSV / external service)
from *how* the agent consumes them (rules + LangChain tools).

The provider returns small JSON-serialisable dicts so they can be passed straight
into the existing tool/audit tracing.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import requests

from guardian.data.scam_db import ScamDatabase


class ScamSignalProvider(ABC):
    @abstractmethod
    def lookup_number(self, number: str) -> dict[str, Any]: ...

    @abstractmethod
    def check_domain(self, text: str) -> dict[str, Any]: ...

    @abstractmethod
    def search_keywords(self, text: str) -> dict[str, Any]: ...


class ScamDbProvider(ScamSignalProvider):
    """Local provider backed by the in-memory :class:`ScamDatabase`."""

    def __init__(self, db: ScamDatabase) -> None:
        self._db = db

    def lookup_number(self, number: str) -> dict[str, Any]:
        raw = (number or "").lower()
        for entry in self._db.bad_numbers():
            if entry.value in raw:
                return {
                    "hit": True,
                    "match": entry.value,
                    "tag": entry.tag,
                    "weight": entry.weight,
                    "note": entry.note,
                    "source": "local",
                }
        return {"hit": False, "source": "local"}

    def check_domain(self, text: str) -> dict[str, Any]:
        lower = (text or "").lower()
        matches: list[dict[str, Any]] = []
        for domain in self._db.bad_domains():
            if domain.value in lower:
                matches.append(
                    {
                        "domain": domain.value,
                        "tag": domain.tag,
                        "weight": domain.weight,
                        "note": domain.note,
                    }
                )
        return {"hit": bool(matches), "matches": matches, "source": "local"}

    def search_keywords(self, text: str) -> dict[str, Any]:
        lower = (text or "").lower()
        hits: list[dict[str, Any]] = []
        total = 0.0
        for keyword in self._db.keywords():
            if keyword.value in lower:
                hits.append(
                    {
                        "keyword": keyword.value,
                        "tag": keyword.tag,
                        "weight": keyword.weight,
                    }
                )
                total += keyword.weight
        return {
            "count": len(hits),
            "total_weight": round(total, 3),
            "hits": hits,
            "source": "local",
        }


class McpScamClient(ScamSignalProvider):
    """HTTP client for the mock MCP scam-signal service."""

    def __init__(self, endpoint: str, *, timeout_s: float = 3.0) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.timeout_s = timeout_s

    def _post(self, route: str, payload: dict[str, Any]) -> dict[str, Any]:
        resp = requests.post(
            f"{self.endpoint}/{route}",
            json=payload,
            timeout=self.timeout_s,
        )
        resp.raise_for_status()
        out = resp.json()
        if isinstance(out, dict):
            out.setdefault("source", "mcp")
        return out

    def health(self) -> bool:
        try:
            resp = requests.get(f"{self.endpoint}/health", timeout=self.timeout_s)
            return resp.status_code == 200
        except Exception:
            return False

    def lookup_number(self, number: str) -> dict[str, Any]:
        return self._post("lookup_number", {"number": number})

    def check_domain(self, text: str) -> dict[str, Any]:
        return self._post("check_domain", {"text": text})

    def search_keywords(self, text: str) -> dict[str, Any]:
        return self._post("search_keywords", {"text": text})


class FallbackProvider(ScamSignalProvider):
    """Try MCP first; fall back to local provider on any failure."""

    def __init__(
        self,
        *,
        mcp: ScamSignalProvider,
        local: ScamSignalProvider,
        strict: bool = False,
    ) -> None:
        self._mcp = mcp
        self._local = local
        self._strict = strict

    def lookup_number(self, number: str) -> dict[str, Any]:
        try:
            return self._mcp.lookup_number(number)
        except Exception:
            if self._strict:
                raise
            out = self._local.lookup_number(number)
            if isinstance(out, dict):
                out["fallback"] = "local"
            return out

    def check_domain(self, text: str) -> dict[str, Any]:
        try:
            return self._mcp.check_domain(text)
        except Exception:
            if self._strict:
                raise
            out = self._local.check_domain(text)
            if isinstance(out, dict):
                out["fallback"] = "local"
            return out

    def search_keywords(self, text: str) -> dict[str, Any]:
        try:
            return self._mcp.search_keywords(text)
        except Exception:
            if self._strict:
                raise
            out = self._local.search_keywords(text)
            if isinstance(out, dict):
                out["fallback"] = "local"
            return out
