"""
Audit feed UI renderer module for real-time security events and Logfire telemetry dashboard.
"""

import streamlit as st


def render_audit_tab():
    """Renders real-time audit log stream, status analytics metrics, filters, and raw telemetry inspection."""
    st.markdown("### 📊 Real-Time Audit Log Feed")
    st.caption("Live security event log stream integrated with Pydantic Logfire & risk scoring analytics.")

    # Logfire Connection Status Banner
    col_lf_status, col_lf_link = st.columns([6, 2])
    with col_lf_status:
        if st.session_state.get("_lf_ready"):
            st.success("🟢 **Logfire Active**: Real-time audit telemetry is being streamed to Pydantic Logfire.")
        else:
            st.warning("⚠️ **Logfire Off**: LOGFIRE_TOKEN missing in .env environment.")
    with col_lf_link:
        st.markdown("[🔗 Open Logfire Cloud](https://logfire.pydantic.dev)", unsafe_allow_html=True)

    st.divider()

    audit_list = st.session_state.get("audit_logs", [])

    # Analytics Overview Metrics
    m1, m2, m3, m4, m5 = st.columns(5)
    total_cnt = len(audit_list)
    blocked_cnt = sum(1 for a in audit_list if a.get("status") == "BLOCKED")
    warned_cnt = sum(1 for a in audit_list if a.get("status") == "WARNED")
    avg_latency = round(sum(a.get("latency_ms", 0) for a in audit_list) / max(total_cnt, 1))
    max_risk = max([a.get("risk_score", 0.0) for a in audit_list], default=0.0)

    m1.metric("Total Events", total_cnt)
    m2.metric("Blocked Requests", blocked_cnt, delta=f"{blocked_cnt}" if blocked_cnt else "0", delta_color="inverse")
    m3.metric("Threat Warnings", warned_cnt, delta=f"{warned_cnt}" if warned_cnt else "0", delta_color="off")
    m4.metric("Avg Latency", f"{avg_latency} ms")
    m5.metric("Max Risk Score", f"{max_risk}/10")

    st.divider()

    # Filter Controls
    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 2, 3, 1])
    with col_f1:
        status_filter = st.selectbox("Status Filter", ["ALL", "RAW_UNGUARDED", "BLOCKED", "WARNED", "ALLOWED"], key="audit_stat_flt")
    with col_f2:
        exp_filter = st.selectbox("Experiment Filter", ["ALL"] + [f"Exp {i}" for i in range(1, 9)], key="audit_exp_flt")
    with col_f3:
        search_query = st.text_input("Search Prompt / Response", placeholder="e.g. deloitte, pii, credit card...", key="audit_search")
    with col_f4:
        st.write("")
        st.write("")
        if st.button("🗑 Clear", key="clear_audit_logs"):
            st.session_state["audit_logs"] = []
            st.rerun()

    # Filter audit entries
    filtered_logs = audit_list
    if status_filter != "ALL":
        filtered_logs = [a for a in filtered_logs if a.get("status") == status_filter]
    if exp_filter != "ALL":
        exp_num_selected = int(exp_filter.replace("Exp ", ""))
        filtered_logs = [a for a in filtered_logs if a.get("experiment_id") == exp_num_selected]
    if search_query.strip():
        sq = search_query.lower()
        filtered_logs = [
            a for a in filtered_logs
            if sq in a.get("prompt", "").lower() or sq in a.get("response", "").lower()
        ]

    if not filtered_logs:
        st.info("No audit events match the selected filters yet. Run prompts in any experiment tab to view live audit events here!")
    else:
        for idx, entry in enumerate(filtered_logs):
            status_symbol = "🔴 RAW" if entry["status"] == "RAW_UNGUARDED" else ("🛑 BLOCKED" if entry["status"] == "BLOCKED" else ("⚠️ WARNED" if entry["status"] == "WARNED" else "✅ ALLOWED"))
            risk_cat = entry.get("risk_category", "UNGUARDED")
            score = entry.get("risk_score", 0.0)
            
            with st.expander(f"{entry['timestamp']} | {status_symbol} | Exp {entry['experiment_id']} | Risk: {score} ({risk_cat}) | ⏱ {entry.get('latency_ms', 0)} ms"):
                st.markdown(f"**User Prompt:**")
                st.code(entry.get("prompt", ""), language="text")
                st.markdown(f"**Bot Response:**")
                st.write(entry.get("response", ""))

                c_meta1, c_meta2 = st.columns(2)
                with c_meta1:
                    st.markdown(f"- **Session ID:** `{entry.get('session_id')}`")
                    st.markdown(f"- **Status:** `{entry.get('status')}`")
                    st.markdown(f"- **Latency:** `{entry.get('latency_ms')} ms`")
                with c_meta2:
                    st.markdown(f"- **PII Detected:** `{entry.get('pii_detected') or 'None'}`")
                    st.markdown(f"- **Urgency Flag:** `{entry.get('urgency_flag')}`")
                    st.markdown(f"- **Threat Vectors:** `{', '.join(entry.get('threat_vectors', []))}`")

                with st.expander("🔍 View Raw Logfire Audit Payload"):
                    st.json(entry)
