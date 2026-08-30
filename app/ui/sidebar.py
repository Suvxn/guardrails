"""
Sidebar UI layout module.
"""

import os
from pathlib import Path
import streamlit as st
import logfire
from dotenv import load_dotenv
from app.models import GROQ_MODELS, GUARD_MODEL_DEFAULT, CHAT_MODEL_DEFAULT

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env", override=True)


def render_sidebar() -> tuple:
    """Renders sidebar controls and returns configured (groq_main, groq_guard, chat_model, guard_model)."""
    with st.sidebar:
        st.title("🛡️ Accenture Control Plane")
        st.caption("Enterprise Brand & Safety Rails Dashboard")
        st.divider()

        # API Status
        groq_main  = os.environ.get("GROQ_API_KEY", "")
        groq_guard = os.environ.get("GROQ_GUARD_KEY", groq_main)
        st.success("✅ API Credentials Active")

        st.divider()
        st.subheader("🤖 Model Selection")

        chat_model = st.selectbox(
            "Chatbot model (Baseline)",
            options=list(GROQ_MODELS.keys()),
            index=list(GROQ_MODELS.keys()).index(CHAT_MODEL_DEFAULT),
            format_func=lambda m: GROQ_MODELS[m],
        )

        guard_model = st.selectbox(
            "Guardrail model (Exp 2–7)",
            options=list(GROQ_MODELS.keys()),
            index=list(GROQ_MODELS.keys()).index(GUARD_MODEL_DEFAULT),
            format_func=lambda m: GROQ_MODELS[m],
        )

        if guard_model == "openai/gpt-oss-20b":
            st.warning("20B models may miss subtle jailbreaks. OpenAI OSS 120B is recommended for guardrails.")

        st.divider()
        st.subheader("📊 Logfire Tracing")
        env_lf_token = os.environ.get("LOGFIRE_TOKEN", "")
        if env_lf_token:
            try:
                logfire.configure(token=env_lf_token, service_name="Accenture Guardrails Control Plane")
                st.session_state["_lf_ready"] = True
                st.success("🟢 Logfire Tracing Active")
            except Exception as e:
                st.error(f"Logfire Error: {e}")
        else:
            st.info("Logfire: Active in background")

    return groq_main, groq_guard, chat_model, guard_model
