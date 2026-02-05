#!/usr/bin/env python3
from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import pandas as pd
import requests

WDQS_URL = "https://query.wikidata.org/sparql"
UA = "PAC-Athlete-Qualifier-Prototype/1.0 (contact: prototype; +https://wikidata.org)"

@dataclass(frozen=True)
class LeagueSpec:
    league: str
    sport: str
    id_property: str
    id_label: str

LEAGUES: Dict[str, LeagueSpec] = {
    "NFL": LeagueSpec("NFL", "American football", "P3561", "pro_football_reference_id"),
    "NBA": LeagueSpec("NBA", "Basketball", "P3647", "nba_com_player_id"),
    "MLB": LeagueSpec("MLB", "Baseball", "P3541", "mlb_com_player_id"),
    "MLS": LeagueSpec("MLS", "Soccer", "P2398", "mls_player_id"),
}

def wdqs_query(query: str, timeout: int = 60) -> dict:
    headers = {"Accept": "application/sparql+json", "User-Agent": UA}
    r = requests.get(WDQS_URL, params={"query": query}, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.json()

def fetch_league(spec: LeagueSpec, limit: int, offset: int = 0) -> pd.DataFrame:
    q = f"""
    SELECT ?item ?itemLabel ?dob ?{spec.id_label} WHERE {{
      ?item wdt:{spec.id_property} ?{spec.id_label} .
      OPTIONAL {{ ?item wdt:P569 ?dob . }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    LIMIT {limit}
    OFFSET {offset}
    """
    data = wdqs_query(q)
    rows = []
    for b in data["results"]["bindings"]:
        qid = b["item"]["value"].rsplit("/", 1)[-1]
        rows.append({
            "qid": qid,
            "name": b.get("itemLabel", {}).get("value"),
            "dob": b.get("dob", {}).get("value"),
            "league": spec.league,
            "sport": spec.sport,
            "league_id": b.get(spec.id_label, {}).get("value"),
            "league_id_property": spec.id_property,
            "proof_wikidata_url": f"https://www.wikidata.org/wiki/{qid}",
            "level": "major",
            "source": "wikidata",
        })
    return pd.DataFrame(rows)

def build_registry(per_league_limit: int, out_dir: Path, sleep_s: float = 0.25) -> pd.DataFrame:
    out_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    for _, spec in LEAGUES.items():
        print(f"[+] Fetching {spec.league} (limit={per_league_limit})")
        frames.append(fetch_league(spec, limit=per_league_limit, offset=0))
        time.sleep(sleep_s)

    athletes = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["league", "league_id", "qid"])
    athletes["name"] = athletes["name"].fillna("").astype(str)
    athletes["dob"] = athletes["dob"].fillna("").astype(str)

    athletes.to_csv(out_dir / "athletes.csv", index=False)

    import sqlite3
    conn = sqlite3.connect(out_dir / "athletes.sqlite")
    athletes.to_sql("athletes", conn, if_exists="replace", index=False)
    conn.close()

    print(f"[✓] Wrote {len(athletes):,} athletes to {out_dir/'athletes.csv'}")
    return athletes

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out-dir", default="data")
    p.add_argument("--per-league-limit", type=int, default=3000)
    args = p.parse_args()

    try:
        build_registry(args.per_league_limit, Path(args.out_dir))
    except requests.exceptions.RequestException as e:
        raise SystemExit(
            "Network error while calling Wikidata. Run this on your machine with internet access.\n"
            "You can still demo the UI using data/athletes_sample.csv.\n\n"
            f"Details: {e}"
        )

if __name__ == "__main__":
    main()
