"""
Experiment UI renderer module for handling individual policy lab tabs and chat interactions.
"""

import asyncio
import time
import traceback
import streamlit as st
import logfire

from app.experiments import EXPERIMENTS, RAILS_STACKED, COLANG_SNIPPETS
from app.diagrams import get_diagram
from app.inference import infer_raw, infer_guarded, lf_span
from app.actions import detect_pii_in_input, classify_urgency, calculate_risk_score, send_firebase_audit_log


def render_experiment(exp_num: int, groq_main: str, groq_guard: str, chat_model: str, guard_model: str):
    """Renders single experiment lab view, flow diagram, top prompt triggers, and interactive execution pipeline."""
    meta = EXPERIMENTS[exp_num]

    # Header
    st.subheader(meta["label"])
    st.markdown(f"**New concept:** `{meta['new_concept']}`")
    st.markdown(meta["desc"])

    # Diagram + Rails Active
    col_diag, col_info = st.columns([5, 3], gap="large")

    with col_diag:
        st.markdown("**Message Flow Diagram**")
        st.graphviz_chart(get_diagram(exp_num), width="stretch")

    with col_info:
        st.markdown("**Active Rails Stack**")
        stacked = RAILS_STACKED[exp_num]
        if stacked:
            for r in stacked:
                st.write(f"✅ {r}")
        else:
            st.write("*None — direct raw LLM call (Unguarded)*")

        st.markdown("**Active Models**")
        if exp_num == 1:
            st.caption(f"Chatbot: `{chat_model}`")
        else:
            st.caption(f"Guardrail: `{guard_model}`")

        with st.expander("📋 Colang Rules & Flows"):
            st.code(COLANG_SNIPPETS[exp_num], language="text")

    st.markdown("---")

    # Categorised example prompts (at top)
    st.markdown("**💡 Example prompts — click Send to execute:**")
    for cat_idx, (category, prompts) in enumerate(meta["prompts"].items()):
        st.caption(category)
        for i, prompt in enumerate(prompts):
            col_text, col_btn = st.columns([8, 1])
            with col_text:
                st.markdown(f"`{prompt}`")
            with col_btn:
                if st.button("▶ Send", key=f"sug_{exp_num}_{cat_idx}_{i}"):
                    st.session_state[f"inject_{exp_num}"] = prompt
                    st.rerun()

    st.markdown("---")

    # Single Unified Prompt Input Bar (Top Only)
    st.markdown("**⌨️ Custom Prompt Input:**")
    placeholder_text = "Type a message to test production guardrails..." if exp_num == 8 else f"Type prompt for Experiment {exp_num}…"

    with st.form(key=f"form_prompt_{exp_num}", clear_on_submit=True):
        col_input, col_submit = st.columns([8, 2])
        with col_input:
            manual_prompt = st.text_input(
                "Prompt Input",
                placeholder=placeholder_text,
                label_visibility="collapsed"
            )
        with col_submit:
            form_submitted = st.form_submit_button("🚀 Execute Prompt")

    # Chat storage initialization
    chat_key = f"chat_{exp_num}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    # Determine user input
    injected = st.session_state.pop(f"inject_{exp_num}", None)
    user_input = injected or (manual_prompt.strip() if form_submitted and manual_prompt.strip() else None)

    # Execute prompt showing question status
    if user_input:
        with st.status(f"⚡ **Executing Prompt:** `{user_input}`", expanded=True) as status:
            with lf_span("chat_interaction", exp_num=exp_num, user_message=user_input, session_id=st.session_state.get("session_id", "")):
                try:
                    st.write(f"❓ **Executing Question:** `{user_input}`")
                    st.write("🤔 **Thinking...**")

                    if exp_num == 1:
                        bot_msg, ms = infer_raw(groq_main, chat_model, user_input)
                        is_blocked = False
                        pii_found = []
                        is_urgent = False
                        risk_meta = {
                            "score": 0.0,
                            "category": "UNGUARDED",
                            "badge_color": "#808080",
                            "threat_vectors": ["Raw LLM Baseline (No Risk Engine Applied)"]
                        }
                        status_label = "RAW_UNGUARDED"
                    else:
                        bot_msg, ms = infer_guarded(groq_guard, guard_model, exp_num, user_input)
                        is_blocked = "can't help" in bot_msg.lower() or "withheld" in bot_msg.lower() or "guidelines" in bot_msg.lower() or "cannot assist" in bot_msg.lower() or "only assist with accenture" in bot_msg.lower()
                        pii_found = asyncio.run(detect_pii_in_input({"user_message": user_input}))
                        is_urgent = asyncio.run(classify_urgency({"user_message": user_input}))
                        risk_meta = calculate_risk_score(user_input, pii_found, is_blocked, is_urgent)
                        status_label = "BLOCKED" if is_blocked else ("WARNED" if is_urgent or pii_found else "ALLOWED")

                    audit_event = {
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "session_id": st.session_state["session_id"][:8],
                        "experiment_id": exp_num,
                        "prompt": user_input,
                        "response": bot_msg,
                        "status": status_label,
                        "pii_detected": pii_found,
                        "urgency_flag": is_urgent,
                        "risk_score": risk_meta["score"],
                        "risk_category": risk_meta["category"],
                        "threat_vectors": risk_meta["threat_vectors"],
                        "latency_ms": ms
                    }
                    send_firebase_audit_log(audit_event)

                    # Emit real-time audit record to Logfire
                    if st.session_state.get("_lf_ready"):
                        if exp_num == 1:
                            logfire.info("Audit Event — Baseline Raw LLM Direct Response", **audit_event)
                        elif is_blocked:
                            logfire.warn("Audit Event — Accenture Policy Refusal Triggered", **audit_event)
                        elif is_urgent or pii_found:
                            logfire.notice("Audit Event — Warning & Threat Vector", **audit_event)
                        else:
                            logfire.info("Audit Event — Clean Request Allowed", **audit_event)

                    # Persist in session audit feed
                    if "audit_logs" not in st.session_state:
                        st.session_state["audit_logs"] = []
                    st.session_state["audit_logs"].insert(0, audit_event)

                    # Store execution pair at TOP of chat list (index 0)
                    exchange_item = {
                        "user": user_input,
                        "assistant": bot_msg,
                        "ms": ms,
                        "risk": risk_meta,
                        "status": status_label,
                        "timestamp": time.strftime("%H:%M:%S")
                    }
                    st.session_state[chat_key].insert(0, exchange_item)

                    status.update(
                        label=f"✅ **Execution Complete** — Status: `{status_label}` (⏱ {ms} ms)",
                        state="complete",
                        expanded=False
                    )

                except Exception as e:
                    status.update(label=f"❌ **Execution Error:** {type(e).__name__}", state="error", expanded=True)
                    st.error(f"**{type(e).__name__}:** {e}")
                    with st.expander("Full traceback"):
                        st.code(traceback.format_exc())

    # Render Execution Log
    if st.session_state[chat_key]:
        st.markdown("---")
        col_log_hdr, col_clear = st.columns([7, 2])
        with col_log_hdr:
            st.markdown("### 💬 Execution Log")
        with col_clear:
            if st.button("🗑 Clear chat history", key=f"clr_{exp_num}"):
                st.session_state[chat_key] = []
                st.rerun()

        for idx, item in enumerate(st.session_state[chat_key]):
            prompt_num = len(st.session_state[chat_key]) - idx
            st.markdown(f"**Prompt #{prompt_num}** `[{item.get('timestamp', '')}]` · **Status:** `{item.get('status', 'ALLOWED')}`")
            with st.chat_message("user"):
                st.write(item["user"])

            with st.chat_message("assistant"):
                st.write(item["assistant"])
                if exp_num == 1:
                    st.caption(f"⏱ {item['ms']} ms · 🔴 Raw LLM Output (Unguarded)")
                else:
                    risk = item.get("risk", {})
                    badge = f" · **Risk:** `{risk.get('category', 'N/A')} ({risk.get('score', 0.0)}/10)`" if risk else ""
                    st.caption(f"⏱ {item['ms']} ms{badge}")
            st.markdown("---")
