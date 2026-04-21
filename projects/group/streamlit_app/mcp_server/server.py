from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI
from pydantic import BaseModel

from guardian.data.scam_db import ScamDatabase
from guardian.data.scam_signals import ScamDbProvider
from guardian.paths import SCAM_DB_CSV

app = FastAPI(title="Guardian Mock MCP Scam DB")


class NumberIn(BaseModel):
    number: str


class TextIn(BaseModel):
    text: str


@lru_cache(maxsize=1)
def _provider() -> ScamDbProvider:
    db = ScamDatabase.from_csv(SCAM_DB_CSV.read_text(encoding="utf-8"))
    return ScamDbProvider(db)


@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": True}


@app.post("/lookup_number")
def lookup_number(payload: NumberIn) -> dict:
    out = _provider().lookup_number(payload.number)
    out["source"] = "mcp"
    out.pop("fallback", None)
    return out


@app.post("/check_domain")
def check_domain(payload: TextIn) -> dict:
    out = _provider().check_domain(payload.text)
    out["source"] = "mcp"
    out.pop("fallback", None)
    return out


@app.post("/search_keywords")
def search_keywords(payload: TextIn) -> dict:
    out = _provider().search_keywords(payload.text)
    out["source"] = "mcp"
    out.pop("fallback", None)
    return out
