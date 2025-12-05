# app.py
"""
FrontDesk Coach v0

Single-turn coaching:
- You describe the situation.
- You paste your draft reply to the guest.
- The AI 'manager' reviews it and suggests better language.
"""

from __future__ import annotations

import os
import asyncio
from typing import Any

import streamlit as st
from dotenv import load_dotenv
import yaml

from agents import Agent, Runner  # from your course framework

# ─────────────────────────────────────────────────────────
# Environment
# ─────────────────────────────────────────────────────────

def get_openai_api_key() -> str:
    """
    1. Load .env (local dev / evaluators). This won't override real env vars.
    2. Read OPENAI_API_KEY from environment (works for Codespaces secrets or .env).
    3. If missing, raise a clear error.
    """
    # Load .env if present (no-op if not)
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set.\n"
            "Set it as a Codespaces secret OR create a .env file with:\n"
            "OPENAI_API_KEY=your_key_here"
        )

    # Ensure downstream libs see it
    os.environ["OPENAI_API_KEY"] = api_key
    return api_key


OPENAI_API_KEY = get_openai_api_key()

# The agents / OpenAI SDK will read OPENAI_API_KEY from the env,
# but setting it explicitly doesn’t hurt:
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────

def load_hotel_profile(path: str = "data/statler_profile.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


HOTEL_PROFILE = load_hotel_profile()


def extract_text(result_obj: Any) -> str:
    """
    Pull a usable string from the Runner result in a tolerant way.
    Same pattern as in assign_2.py.
    """
    return (
        getattr(result_obj, "final_output", None)
        or getattr(result_obj, "text", None)
        or str(result_obj)
    )


# ─────────────────────────────────────────────────────────
# Coach Agent
# ─────────────────────────────────────────────────────────

COACH_INSTRUCTIONS = """
You are a seasoned front-office manager at a high-end hotel.

You coach new front-desk associates on their written replies to guests.
You always:
- Respect the hotel's tone guidelines.
- Respect the hotel's policies as given in context.
- Focus on language and explanation, not changing the underlying decision.

Your tasks:
1. Briefly score the reply on:
   - Policy adherence (1–5)
   - Tone / empathy (1–5)
   - Clarity / usefulness (1–5)
2. Point out 1–3 concrete things they did well.
3. Point out 1–3 concrete things to improve.
4. Rewrite their reply so it:
   - Keeps the same decision (e.g., waive fee or not),
   - Uses warmer, clearer language aligned with the tone guidelines.

Answer in markdown with three sections:
- **Quick scores**
- **Feedback**
- **Suggested rewrite**
"""

coach_agent = Agent(
    name="Coach Agent",
    model="openai.gpt-4o",   # or whatever model your group key supports
    instructions=COACH_INSTRUCTIONS.strip(),
)


def build_context() -> str:
    tone = "\n".join(HOTEL_PROFILE.get("tone_guidelines", []))

    policies_txt = []
    for name, cfg in HOTEL_PROFILE.get("policies", {}).items():
        policies_txt.append(f"Policy: {name}")
        summary = cfg.get("summary")
        if summary:
            policies_txt.append(f"  Summary: {summary}")
    policies_block = "\n".join(policies_txt)

    good_phrases = "\n".join(HOTEL_PROFILE.get("good_phrases", []))
    bad_phrases = "\n".join(HOTEL_PROFILE.get("phrases_to_avoid", []))

    return f"""
Tone guidelines:
{tone}

Key policies:
{policies_block}

Phrases to avoid:
{bad_phrases}

Preferred phrases:
{good_phrases}
""".strip()


def run_coach(situation: str, trainee_reply: str) -> str:
    context = build_context()

    user_msg = f"""
Situation:
{ situation }

Hotel context:
{ context }

Associate's draft reply:
\"\"\"{ trainee_reply }\"\"\"
"""

    result = asyncio.run(Runner.run(coach_agent, user_msg))
    return extract_text(result)


# ─────────────────────────────────────────────────────────
# Streamlit UI
# ─────────────────────────────────────────────────────────

st.set_page_config(page_title="FrontDesk Coach", page_icon="🛎️")
st.title("🛎️ FrontDesk Coach (v0)")
st.caption("Practice your front-desk replies and get AI manager coaching.")

default_situation = "Guest is upset about being charged a no-show fee after claiming they cancelled."
situation = st.text_input("Scenario / situation:", value=default_situation)

trainee_reply = st.text_area("Your draft reply to the guest:", height=200)

if st.button("Get coaching", type="primary"):
    if not trainee_reply.strip():
        st.warning("Type a reply first.")
    else:
        with st.spinner("Asking your (very patient) manager for feedback..."):
            feedback = run_coach(situation, trainee_reply)

        st.markdown("### Coach Feedback")
        st.markdown(feedback)