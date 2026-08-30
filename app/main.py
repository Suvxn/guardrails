import sys
import uuid
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

# Ensure root directory and app/ directory are on Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

load_dotenv(BASE_DIR / ".env", override=True)

from app.ui.sidebar import render_sidebar
from app.ui.experiment_ui import render_experiment
from app.ui.audit_ui import render_audit_tab

# ─────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Accenture Guardrails Control Plane",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Session tracking
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

# Render sidebar & capture API/model options
groq_main, groq_guard, chat_model, guard_model = render_sidebar()


st.title("🛡️ Accenture Guardrails Enterprise Control Plane")
st.caption("8 progressive experiments · brand protection & compliance policy · real-time Logfire telemetry")
st.divider()

tab_baseline, tab_input, tab_custom, tab_output, tab_production, tab_audit = st.tabs([
    "🔴 Baseline",
    "📥 Input Rails",
    "⚙️ Custom Actions",
    "📤 Output Rails",
    "🛡️ Full Production Stack",
    "📊 Real-Time Audit Feed",
])

with tab_baseline:
    st.markdown("### The Problem — Raw LLM with No Protection")
    st.markdown("Run any prompt below to see how an unguarded LLM responds to competitor comparisons, financial advice, or code requests.")
    render_experiment(1, groq_main, groq_guard, chat_model, guard_model)

with tab_input:
    st.markdown("### 📥 Input Rails")
    st.markdown("Input rails intercept messages **before they reach the LLM**.")
    st.divider()

    sub_input = st.radio(
        "Choose experiment:",
        options=[2, 3, 4, 5],
        format_func=lambda x: {
            2: "🟡 Exp 2 — Topic Guard",
            3: "🟡 Exp 3 — Jailbreak Shield",
            4: "🟡 Exp 4 — Sensitive & Policy Block",
            5: "🟢 Exp 5 — Dialog Rails",
        }[x],
        horizontal=True,
        key="input_rail_sub",
    )
    render_experiment(sub_input, groq_main, groq_guard, chat_model, guard_model)

with tab_custom:
    st.markdown("### ⚙️ Custom Python Actions")
    st.markdown("Custom actions bridge Python logic and Colang flows via the `@action` decorator.")
    render_experiment(6, groq_main, groq_guard, chat_model, guard_model)

with tab_output:
    st.markdown("### 📤 Output Rails")
    st.markdown("Output rails intercept LLM responses **before the user sees them**.")
    render_experiment(7, groq_main, groq_guard, chat_model, guard_model)

with tab_production:
    st.markdown("### 🛡️ Production Playground")
    st.caption("Full enterprise guardrail stack running in production mode.")
    render_experiment(8, groq_main, groq_guard, chat_model, guard_model)

with tab_audit:
    render_audit_tab()

