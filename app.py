import streamlit as st
from dataclasses import dataclass, asdict
from typing import List, Dict, Tuple

# -----------------------------
# 1. Page Configuration & Style
# -----------------------------
st.set_page_config(
    page_title="PhaseShift — Adoption Transition Engine",
    page_icon="🧭",
    layout="wide"
)

# Custom CSS for a "Premium" feel
st.markdown("""
    <style>
    .main { background-color: #fcfcfc; }
    .stMetric { border: 1px solid #eee; padding: 10px; border-radius: 8px; background: white; }
    .reportview-container .main .block-container { padding-top: 2rem; }
    </style>
    """, unsafe_allow_stdio=True)

# -----------------------------
# 2. Data Model & Engine
# -----------------------------
@dataclass
class Intake:
    one_liner: str
    who_for: str
    current_users: str
    acquisition_channel: str
    pricing: str
    headline: str
    proof_assets: List[str]
    traction_stage: str
    growth_blocker: str

class PhaseShiftEngine:
    """Encapsulates all scoring and diagnostic logic."""
    
    # Weights and Cues (Moved from global to class constants)
    PROOF_WEIGHTS = {"case studies": 10, "testimonials": 8, "logos": 5, "ROI numbers": 12, "security/compliance": 10, "none": 0}
    PRICING_WEIGHTS = {"free": 10, "freemium": 8, "$/mo": 4, "enterprise": 2}
    TRACTION_WEIGHTS = {"pre-launch": 2, "0–100 users": 4, "100–1k": 7, "1k–10k": 10, "10k+": 12}
    CHANNEL_WEIGHTS = {"Twitter/LinkedIn": 4, "community": 5, "paid ads": 7, "outbound": 6, "partnerships": 8, "app store": 7, "other": 5}
    BLOCKER_PENALTY = {"messaging": 6, "trust": 10, "onboarding": 8, "pricing": 7, "unclear ICP": 10, "feature sprawl": 7, "switching costs": 9}
    
    EM_CUES = ["reliable", "predictable", "secure", "compliant", "workflow", "roi", "save time", "reduce", "risk", "integrate"]
    EA_CUES = ["cutting-edge", "state-of-the-art", "agent", "autonomous", "revolution", "transform", "magic", "vibe"]

    @classmethod
    def analyze(cls, intake: Intake) -> Dict:
        # 1. Calculate Keyword Cues
        text = (intake.headline + " " + intake.one_liner).lower()
        em_hits = sum(1 for w in cls.EM_CUES if w in text)
        ea_hits = sum(1 for w in cls.EA_CUES if w in text)

        # 2. Score Components
        proof_score = min(sum(cls.PROOF_WEIGHTS.get(p, 0) for p in intake.proof_assets), 25)
        pricing_score = cls.PRICING_WEIGHTS.get(intake.pricing, 4)
        traction_score = cls.TRACTION_WEIGHTS.get(intake.traction_stage, 4)
        channel_score = cls.CHANNEL_WEIGHTS.get(intake.acquisition_channel, 5)
        
        # ICP Logic
        icp_len = len(intake.who_for.split())
        icp_score = 5 if icp_len >= 6 else 2
        if any(x in intake.who_for.lower() for x in ["everyone", "anyone", "all"]):
            icp_score = 1

        # 3. Final Aggregation
        readiness = (proof_score + (em_hits * 4) + pricing_score + traction_score + channel_score + icp_score)
        readiness -= (cls.BLOCKER_PENALTY.get(intake.growth_blocker, 6) + (ea_hits * 3))
        
        final_score = max(0, min(int(readiness * 2), 100))
        risk = 100 - final_score
        
        return {
            "readiness": final_score,
            "risk": risk,
            "em_hits": em_hits,
            "ea_hits": ea_hits,
            "proof_pts": proof_score
        }

# -----------------------------
# 3. UI Application
# -----------------------------
st.title("🧭 PhaseShift")
st.caption("Strategic Adoption Transition Engine for AI Startups")

# --- SIDEBAR INTAKE ---
with st.sidebar:
    st.header("1. Product Intake")
    with st.form("intake_form"):
        one_liner = st.text_area("Product one-liner", placeholder="AI agent for support...", height=80)
        who_for = st.text_input("Who it’s for", placeholder="B2B SaaS support teams...")
        headline = st.text_input("Landing Page Headline")
        
        st.divider()
        
        current_users = st.selectbox("Current Users", ["Innovators", "Early Adopters", "Mixed", "Unsure"])
        channel = st.selectbox("Top Acquisition Channel", list(PhaseShiftEngine.CHANNEL_WEIGHTS.keys()))
        pricing = st.selectbox("Pricing Model", list(PhaseShiftEngine.PRICING_WEIGHTS.keys()))
        traction = st.selectbox("Traction Stage", list(PhaseShiftEngine.TRACTION_WEIGHTS.keys()))
        blocker = st.selectbox("Growth Blocker", list(PhaseShiftEngine.BLOCKER_PENALTY.keys()))
        proof = st.multiselect("Proof Assets", list(PhaseShiftEngine.PROOF_WEIGHTS.keys()), default=["none"])
        
        submitted = st.form_submit_button("Run Diagnosis", type="primary", use_container_width=True)

# --- MAIN STAGE RESULTS ---
if submitted:
    # Instantiate and Run Analysis
    data = Intake(one_liner, who_for, current_users, channel, pricing, headline, proof, traction, blocker)
    results = PhaseShiftEngine.analyze(data)
    
    # A. Metric Dashboard
    col1, col2, col3 = st.columns(3)
    col1.metric("Mainstream Readiness", f"{results['readiness']}%")
    
    risk_level = "High" if results['risk'] > 60 else "Medium" if results['risk'] > 30 else "Low"
    col2.metric("Chasm Risk", f"{risk_level} ({results['risk']}%)")
    
    confidence = "High" if results['readiness'] > 70 else "Low"
    col3.metric("Data Confidence", confidence)

    st.progress(results['readiness'] / 100, text="Readiness Progress Bar")
    
    st.divider()

    # B. Detailed Analysis Tabs
    tab1, tab2, tab3 = st.tabs(["🔍 Market Diagnosis", "🚀 Action Plan", "📊 Score Breakdown"])

    with tab1:
        st.subheader("Current Market Segment")
        # Logic for segment naming based on your original classify_segment
        if results['readiness'] <= 45:
            st.warning("Current Segment: **Innovators / Visionaries**")
        elif results['readiness'] <= 70:
            st.info("Current Segment: **Early Adopter Chasm Zone**")
        else:
            st.success("Current Segment: **Early Majority Ready**")

        st.markdown(f"**Growth Blocker Impact:** Your focus on `{blocker}` is acting as a significant friction point for mainstream adoption.")

    with tab2:
        st.subheader("The 'Crossing the Chasm' Plan")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 📝 Messaging Shift")
            st.write("- Transition from **capability** to **outcome**.")
            st.write("- Highlight reliability over 'newness'.")
        with c2:
            st.markdown("### 🛡️ Trust Strategy")
            st.write(f"- Increase proof assets from current level (Score: {results['proof_pts']}/25).")
            st.write("- Prioritize security and compliance documentation.")

    with tab3:
        st.write("Raw scoring data for transparency:")
        st.json(results)

else:
    st.info("Please fill out the intake form in the sidebar and click 'Run Diagnosis' to begin.")
