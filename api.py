from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd

from matcher import match_lead

app = FastAPI(title="PAC Athlete Lead Qualifier (Prototype)")
REGISTRY_PATH = "data/athletes_sample.csv"

def load_registry() -> pd.DataFrame:
    return pd.read_csv(REGISTRY_PATH)

class Lead(BaseModel):
    name: str
    dob: str | None = None
    league_hint: str | None = None

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/match")
def match(lead: Lead):
    athletes = load_registry()
    res = match_lead(athletes, lead_name=lead.name, lead_dob=lead.dob, league_hint=lead.league_hint, top_k=5)
    return {
        "is_probable_pro": res.is_probable_pro,
        "confidence": res.confidence,
        "reasons": res.reasons,
        "matches": res.matches,
    }
