# PAC Athlete Lead Qualifier (Prototype)

This prototype helps PAC pre-qualify inbound leads by matching a name to a public athlete registry.

**Prototype scope:** NFL / NBA / MLB / MLS (no Olympics)

## What you get
- `build_registry.py` — pulls athletes from Wikidata (SPARQL) into a single registry table
- `matcher.py` — name normalization + fuzzy matching + confidence scoring
- `app.py` — Streamlit demo UI (fastest way to show this in an interview)
- `api.py` — optional FastAPI endpoint

## Why the repo includes a small sample CSV
This sandbox environment can't reach the public internet from Python, so I bundled a small `data/athletes_sample.csv` so the UI works immediately.
On your machine, run `build_registry.py` to generate a real registry from Wikidata.

## Install
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Run the demo UI (using the bundled sample)
```bash
streamlit run app.py
```
In the app, set **Registry CSV path** to:
- `data/athletes_sample.csv` (works immediately)

## Build the real registry (on your machine, with internet)
```bash
python build_registry.py --out-dir data --per-league-limit 3000
# then point the app to: data/athletes.csv
```

## How it scales to feeder leagues (your interview soundbite)
- The matcher is source-agnostic: every league ingests into the same schema.
- Adding feeder leagues = add a new connector that emits the same columns, set `level='feeder'`.
- Disambiguation improves by enriching attributes (DOB, team history, position, last active year).

## Wikidata properties used
- NFL: Pro-Football-Reference player ID (P3561)
- NBA: NBA.com player ID (P3647)
- MLB: MLB.com player ID (P3541)
- MLS: MLS player ID (P2398)
