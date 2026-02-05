import pandas as pd
import streamlit as st

from matcher import match_lead

st.set_page_config(page_title="PAC Athlete Lead Qualifier (Prototype)", layout="wide")

st.title("PAC Athlete Lead Qualifier (Prototype)")
st.caption("Paste a lead name and get a confidence-scored match + proof link. (Prototype scope: NFL/NBA/MLB/MLS)")

@st.cache_data(show_spinner=False)
def load_registry(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    lead_name = st.text_input("Lead name", placeholder="e.g., LeBron James")
with col2:
    lead_dob = st.text_input("DOB (optional, ISO)", placeholder="YYYY-MM-DD")
with col3:
    league_hint = st.selectbox("League hint (optional)", ["", "NFL", "NBA", "MLB", "MLS"])

registry_path = st.text_input("Registry CSV path", value="data/athletes_sample.csv")

if st.button("Match lead", type="primary"):
    try:
        athletes = load_registry(registry_path)
    except Exception as e:
        st.error(f"Couldn't load registry at '{registry_path}'.")
        st.exception(e)
        st.stop()

    result = match_lead(
        athletes,
        lead_name=lead_name,
        lead_dob=lead_dob or None,
        league_hint=league_hint or None,
        top_k=5,
    )

    st.subheader("Result")
    st.metric("Probable pro athlete?", "YES" if result.is_probable_pro else "NO", f"{result.confidence}/100")

    for r in result.reasons:
        st.write(f"- {r}")

    st.subheader("Top matches")
    if not result.matches:
        st.info("No matches returned.")
    else:
        st.dataframe(pd.DataFrame(result.matches).sort_values("confidence", ascending=False), use_container_width=True)
