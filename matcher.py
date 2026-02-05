from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

import pandas as pd
from rapidfuzz import fuzz, process

_SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v"}
_PUNCT_RE = re.compile(r"[^a-z0-9\s'-]+")

def normalize_name(name: str) -> str:
    if not name:
        return ""
    s = name.strip().lower()
    s = _PUNCT_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    parts = s.split(" ")
    if parts and parts[-1].replace(".", "") in _SUFFIXES:
        parts = parts[:-1]
    return " ".join(parts)

@dataclass
class MatchResult:
    is_probable_pro: bool
    confidence: int
    matches: List[dict]
    reasons: List[str]

def match_lead(
    athletes: pd.DataFrame,
    lead_name: str,
    lead_dob: Optional[str] = None,
    league_hint: Optional[str] = None,
    top_k: int = 5,
) -> MatchResult:
    if athletes is None or athletes.empty:
        return MatchResult(False, 0, [], ["Registry is empty. Build it first."])

    q = normalize_name(lead_name)
    if not q or len(q) < 3:
        return MatchResult(False, 0, [], ["Lead name is too short to match reliably."])

    df = athletes
    reasons: List[str] = []

    if league_hint:
        league_hint_u = league_hint.strip().upper()
        df = df[df["league"].astype(str).str.upper() == league_hint_u]
        reasons.append(f"Applied league hint filter: {league_hint_u}")

    df = df.copy()
    df["name_norm"] = df["name"].astype(str).map(normalize_name)

    choices = df["name_norm"].tolist()
    extracted = process.extract(q, choices, scorer=fuzz.token_set_ratio, limit=top_k)

    matches: List[dict] = []
    best = 0

    for _, score, idx in extracted:
        row = df.iloc[idx].to_dict()
        best = max(best, int(score))

        dob_boost = 0
        if lead_dob and str(lead_dob).strip():
            if str(row.get("dob", "")).startswith(str(lead_dob).strip()):
                dob_boost = 10

        conf = min(100, int(score) + dob_boost)
        matches.append({
            "confidence": conf,
            "name": row.get("name"),
            "league": row.get("league"),
            "sport": row.get("sport"),
            "dob": row.get("dob") or None,
            "qid": row.get("qid"),
            "proof_wikidata_url": row.get("proof_wikidata_url"),
            "league_id": row.get("league_id"),
            "league_id_property": row.get("league_id_property"),
            "level": row.get("level", "major"),
            "source": row.get("source", ""),
        })

    if best >= 92:
        is_pro = True
        reasons.append("High-confidence name match (>=92).")
    elif best >= 85:
        is_pro = True
        reasons.append("Moderate-confidence name match (85–91). Add DOB/team to disambiguate common names.")
    else:
        is_pro = False
        reasons.append("No sufficiently strong match found (<85).")

    return MatchResult(is_pro, best, matches, reasons)
