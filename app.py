

# app.py
import streamlit as st
from dataclasses import dataclass
from typing import List, Dict, Tuple

# -----------------------------
# PhaseShift — Streamlit MVP
# -----------------------------

st.set_page_config(
    page_title="PhaseShift — Adoption Transition Engine",
    page_icon="🧭",
    layout="wide"
)

st.title("🧭 PhaseShift")
st.caption("Adoption Transition Engine for AI startups — diagnose your current adopter segment and get a strategic plan to reach the Early Majority.")


# -----------------------------
# Data model
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


# -----------------------------
# Scoring + diagnosis logic
# -----------------------------
PROOF_WEIGHTS = {
    "case studies": 10,
    "testimonials": 8,
    "logos": 5,
    "ROI numbers": 12,
    "security/compliance": 10,
    "none": 0,
}

PRICING_WEIGHTS = {
    "free": 10,        # low perceived risk
    "freemium": 8,
    "$/mo": 4,
    "enterprise": 2,
}

TRACTION_WEIGHTS = {
    "pre-launch": 2,
    "0–100 users": 4,
    "100–1k": 7,
    "1k–10k": 10,
    "10k+": 12,
}

CHANNEL_WEIGHTS = {
    "Twitter/LinkedIn": 4,   # tends to skew early adopters
    "community": 5,
    "paid ads": 7,           # can reach broader audience if positioned well
    "outbound": 6,
    "partnerships": 8,       # trust transfer
    "app store": 7,
    "other": 5,
}

BLOCKER_PENALTY = {
    "messaging": 6,
    "trust": 10,
    "onboarding": 8,
    "pricing": 7,
    "unclear ICP": 10,
    "feature sprawl": 7,
    "switching costs": 9,
}

EARLY_MAJORITY_CUES = [
    "reliable", "predictable", "secure", "compliant", "workflow", "roi", "save time",
    "reduce", "improve", "increase", "automate", "cost", "risk", "integrate", "slack",
    "salesforce", "hubspot", "zapier"
]
EARLY_ADOPTER_CUES = [
    "cutting-edge", "state-of-the-art", "agent", "autonomous", "revolution", "transform",
    "breakthrough", "novel", "bleeding edge", "vibe", "magic", "prompt", "copilot"
]

def normalize(text: str) -> str:
    return (text or "").strip().lower()

def cue_score(text: str) -> Tuple[int, int]:
    """
    Returns (early_majority_signal, early_adopter_signal) based on keyword hits.
    Simple heuristic: enough to feel plausible under time crunch.
    """
    t = normalize(text)
    em = sum(1 for w in EARLY_MAJORITY_CUES if w in t)
    ea = sum(1 for w in EARLY_ADOPTER_CUES if w in t)
    return em, ea

def compute_scores(intake: Intake) -> Dict[str, int]:
    # Proof score
    proof_score = sum(PROOF_WEIGHTS.get(p, 0) for p in intake.proof_assets)
    proof_score = min(proof_score, 25)  # cap so it doesn't dominate

    # Pricing score
    pricing_score = PRICING_WEIGHTS.get(intake.pricing, 4)

    # Traction score
    traction_score = TRACTION_WEIGHTS.get(intake.traction_stage, 4)

    # Channel score
    channel_score = CHANNEL_WEIGHTS.get(intake.acquisition_channel, 5)

    # Headline clarity signals
    em_cues, ea_cues = cue_score(intake.headline + " " + intake.one_liner)
    # Translate cue counts into points
    outcome_clarity_score = min(em_cues * 4, 20)  # early-majority cues drive clarity
    novelty_bias_penalty = min(ea_cues * 3, 12)   # early-adopter language can hurt mainstream

    # ICP specificity heuristic: longer + concrete tends to be better than vague
    who_len = len(normalize(intake.who_for).split())
    icp_score = 5 if who_len >= 6 else 2
    if any(x in normalize(intake.who_for) for x in ["everyone", "anyone", "all", "any business"]):
        icp_score = 1  # too broad

    # Blocker penalty
    blocker_penalty = BLOCKER_PENALTY.get(intake.growth_blocker, 6)

    # Base score for mainstream readiness
    # (Transparent rubric: proof + clarity + low risk + traction + channel + icp) - penalties
    readiness = (
        proof_score
        + outcome_clarity_score
        + pricing_score
        + traction_score
        + channel_score
        + icp_score
        - blocker_penalty
        - novelty_bias_penalty
    )

    readiness = max(0, min(int(readiness * 2), 100))  # scale into 0–100
    # Chasm risk is inverse-ish, but we also bump risk if trust/ICP/switching costs are blockers
    risk = 100 - readiness
    if intake.growth_blocker in ["trust", "unclear ICP", "switching costs"]:
        risk = min(100, risk + 10)

    return {
        "readiness": readiness,
        "risk": max(0, min(risk, 100)),
        "proof_score": proof_score,
        "outcome_clarity_score": outcome_clarity_score,
        "novelty_bias_penalty": novelty_bias_penalty,
        "pricing_score": pricing_score,
        "traction_score": traction_score,
        "channel_score": channel_score,
        "icp_score": icp_score,
        "blocker_penalty": blocker_penalty,
        "em_cues": em_cues,
        "ea_cues": ea_cues,
    }

def classify_segment(intake: Intake, readiness: int) -> str:
    # Use readiness + their self-reported current user type for a plausible classification
    self_report = intake.current_users
    if readiness <= 40:
        base = "Innovators"
    elif readiness <= 65:
        base = "Early Adopters"
    else:
        base = "Early Majority-ready"

    # If they self-report strongly, lightly bias (but don't override extremes)
    if self_report == "Innovators" and readiness <= 55:
        return "Innovators"
    if self_report == "Early Adopters" and readiness <= 75:
        return "Early Adopters"
    if self_report == "Mixed" and 35 <= readiness <= 75:
        return "Chasm Zone (Mixed Signals)"
    if self_report == "Unsure" and 45 <= readiness <= 70:
        return "Chasm Zone (Needs Positioning Tightening)"

    return base

def blocker_insights(intake: Intake, scores: Dict[str, int]) -> List[str]:
    # 3 crisp bullets, strategic coach tone
    bullets = []

    # Proof / trust
    if "none" in intake.proof_assets or scores["proof_score"] <= 6 or intake.growth_blocker == "trust":
        bullets.append("Your trust signals are lighter than the buyer’s perceived risk (proof, security, and credible outcomes need to lead).")

    # Messaging / clarity
    if scores["outcome_clarity_score"] <= 8 or intake.growth_blocker == "messaging":
        bullets.append("Your value proposition reads more like capability than outcome—mainstream buyers need a specific promised result, not possibility.")

    # ICP
    if scores["icp_score"] <= 2 or intake.growth_blocker == "unclear ICP":
        bullets.append("Your ICP is too broad to feel safe—Early Majority responds to “built for people like me,” not “for everyone.”")

    # Onboarding / activation
    if intake.growth_blocker == "onboarding":
        bullets.append("Your product likely asks users to explore—Early Majority needs a guided ‘golden path’ that guarantees a first win fast.")

    # Pricing / switching costs
    if intake.growth_blocker in ["pricing", "switching costs"]:
        bullets.append("The perceived switching cost is higher than the perceived upside—reduce risk with trials, reversibility, and proof-first onboarding.")

    # Novelty language penalty
    if scores["novelty_bias_penalty"] >= 6:
        bullets.append("Your narrative leans ‘new + exciting’—Early Majority wants ‘reliable + proven’ with measurable outcomes.")

    # Ensure exactly 3, prioritize the most important
    if len(bullets) < 3:
        bullets.append("Your acquisition channel may be feeding early adopters—consider distribution that carries trust transfer (partners, integrations, referrals).")

    return bullets[:3]

def transition_plan(intake: Intake, scores: Dict[str, int]) -> Dict[str, List[str]]:
    # Positioning, Proof, Product shifts (strategy, not copy)
    positioning = [
        "Shift from visionary language to operational outcomes (time saved, revenue gained, risk reduced).",
        "Anchor the message on one primary use case (avoid feature laundry lists).",
        "Make the promise time-bound: ‘Get X in 14 days’ or ‘Cut Y by 30%’ (if defensible).",
    ]

    proof = [
        "Add 2 mini case studies (before → after) with quantified results.",
        "Add a ‘How it works’ flow that shows predictability (3 steps, no magic).",
        "Add risk reducers: trial, clear data handling, security/compliance page (even if lightweight).",
    ]

    product = [
        "Design a ‘golden path’ onboarding that reaches one measurable success milestone fast.",
        "Add templates/defaults for the top 1–2 mainstream workflows (reduce setup thinking).",
        "Instrument activation + time-to-first-value so you can iterate toward repeatable adoption.",
    ]

    # Tailor slightly
    if intake.pricing == "enterprise":
        proof.insert(0, "Enterprise buyers need procurement confidence: security posture, data handling, and reliability should be front-and-center.")
    if intake.acquisition_channel in ["Twitter/LinkedIn", "community"]:
        positioning.insert(0, "Your current distribution skews early adopters; reposition for mainstream channels with higher trust transfer (partners, reviews, referrals).")
    if intake.growth_blocker == "feature sprawl":
        product.insert(0, "Cut scope: protect one core workflow and remove/park anything that doesn’t improve activation or retention.")

    return {"Positioning shift": positioning, "Proof shift": proof, "Product shift": product}

def risk_label(risk: int) -> str:
    if risk >= 70:
        return "High"
    if risk >= 45:
        return "Medium"
    return "Low"

def confidence_label(readiness: int) -> str:
    if readiness >= 70:
        return "High"
    if readiness >= 45:
        return "Medium"
    return "Low"


# -----------------------------
# UI Layout
# -----------------------------
left, right = st.columns([1, 1], gap="large")

with left:
    st.subheader("1) Intake")

    one_liner = st.text_area("Product one-liner", placeholder="e.g., An AI agent that drafts customer support responses using your knowledge base.", height=80)
    who_for = st.text_area("Who it’s for", placeholder="e.g., Support teams at B2B SaaS companies with 10–100 agents.", height=70)

    current_users = st.selectbox(
        "Current users you attract most",
        ["Innovators", "Early Adopters", "Mixed", "Unsure"]
    )

    acquisition_channel = st.selectbox(
        "Top acquisition channel",
        ["Twitter/LinkedIn", "community", "paid ads", "outbound", "partnerships", "app store", "other"]
    )

    pricing = st.selectbox(
        "Pricing",
        ["free", "freemium", "$/mo", "enterprise"]
    )

    headline = st.text_input(
        "Current landing page headline",
        placeholder="e.g., Automate repetitive support work and cut ticket resolution time by 30%."
    )

    proof_assets = st.multiselect(
        "Proof assets",
        ["case studies", "testimonials", "logos", "ROI numbers", "security/compliance", "none"],
        default=["none"]
    )

    traction_stage = st.selectbox(
        "Traction stage",
        ["pre-launch", "0–100 users", "100–1k", "1k–10k", "10k+"]
    )

    growth_blocker = st.selectbox(
        "Biggest growth blocker",
        ["messaging", "trust", "onboarding", "pricing", "unclear ICP", "feature sprawl", "switching costs"]
    )

    run = st.button("Run Diagnosis", type="primary", use_container_width=True)

with right:
    st.subheader("2) Diagnosis")

    if not run:
        st.info("Fill out the intake on the left and click **Run Diagnosis**.")
    else:
        intake = Intake(
            one_liner=one_liner,
            who_for=who_for,
            current_users=current_users,
            acquisition_channel=acquisition_channel,
            pricing=pricing,
            headline=headline,
            proof_assets=proof_assets,
            traction_stage=traction_stage,
            growth_blocker=growth_blocker,
        )

        scores = compute_scores(intake)
        segment = classify_segment(intake, scores["readiness"])
        bullets = blocker_insights(intake, scores)
        plan = transition_plan(intake, scores)

        # Top metrics row
        m1, m2, m3 = st.columns(3)
        m1.metric("Mainstream Readiness", f"{scores['readiness']}/100")
        m2.metric("Chasm Risk", f"{risk_label(scores['risk'])} ({scores['risk']}/100)")
        m3.metric("Next-Move Confidence", confidence_label(scores["readiness"]))

        st.markdown("---")

        # Segment
        st.markdown(f"### Segment Diagnosis: **{segment}**")
        rationale = []
        if scores["outcome_clarity_score"] <= 8:
            rationale.append("headline is capability-heavy vs outcome-specific")
        if scores["proof_score"] <= 6:
            rationale.append("proof signals are light relative to perceived risk")
        if scores["novelty_bias_penalty"] >= 6:
            rationale.append("narrative skews toward early-adopter novelty language")
        if scores["icp_score"] <= 2:
            rationale.append("ICP is broad; mainstream buyers need ‘built for me’ specificity")

        if not rationale:
            rationale.append("positioning + proof + traction signals suggest readiness to broaden beyond early adopters")

        st.write("**Why:** " + "; ".join(rationale) + ".")

        # Chasm causes
        st.markdown("### Top blockers (what’s keeping you from Early Majority)")
        for b in bullets:
            st.write(f"- {b}")

        # Transition plan
        st.markdown("### Transition Plan (Early Adopters → Early Majority)")
        for section, items in plan.items():
            with st.expander(section, expanded=True):
                for item in items:
                    st.write(f"- {item}")

        # Optional: show rubric transparency
        with st.expander("Show scoring breakdown (transparent rubric)", expanded=False):
            st.write({
                "proof_score (cap 25)": scores["proof_score"],
                "outcome_clarity_score (cap 20)": scores["outcome_clarity_score"],
                "novelty_bias_penalty (cap 12)": scores["novelty_bias_penalty"],
                "pricing_score": scores["pricing_score"],
                "traction_score": scores["traction_score"],
                "channel_score": scores["channel_score"],
                "icp_score": scores["icp_score"],
                "blocker_penalty": scores["blocker_penalty"],
                "early_majority_cues": scores["em_cues"],
                "early_adopter_cues": scores["ea_cues"],
            })

st.markdown("---")
st.caption("PhaseShift MVP uses a transparent rubric + heuristic signals to produce a strategic coaching plan. You can later swap the heuristics for an LLM-based evaluator if desired.")
