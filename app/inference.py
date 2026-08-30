"""
LLM inference runners, NeMo rails configuration, and Logfire span helpers.
"""

import asyncio
import time
import io
import logging
from pathlib import Path
from contextlib import nullcontext
from concurrent.futures import ThreadPoolExecutor
import streamlit as st
import logfire
from langchain_groq import ChatGroq
from nemoguardrails import RailsConfig, LLMRails

from app.models import SYSTEM_PROMPT_RAW
from app.actions import detect_pii_in_input, classify_urgency, sanitize_output

BASE_DIR = Path(__file__).resolve().parent.parent
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="nemo")


def lf_span(name: str, **kw):
    """Returns a real logfire span when tracing is active, otherwise a no-op."""
    return logfire.span(name, **kw) if st.session_state.get("_lf_ready") else nullcontext()


@st.cache_resource
def load_guardrails_config():
    """Loads NeMo Guardrails YAML & Colang configuration."""
    config_dir = BASE_DIR / "app" / "config"
    return RailsConfig.from_path(str(config_dir))


def build_control_plane_rails(llm):
    """Initialises LLMRails engine and registers custom Python actions."""
    config = load_guardrails_config()
    rails = LLMRails(config=config, llm=llm)
    rails.register_action(detect_pii_in_input)
    rails.register_action(classify_urgency)
    rails.register_action(sanitize_output)
    return rails


def infer_raw(api_key: str, model_name: str, message: str) -> tuple:
    """Executes a direct raw LLM call without guardrails."""
    t0   = time.time()
    llm  = ChatGroq(api_key=api_key, model=model_name, temperature=0)
    resp = llm.invoke([
        {"role": "system", "content": SYSTEM_PROMPT_RAW},
        {"role": "user",   "content": message},
    ])
    return resp.content, round((time.time() - t0) * 1000)


def infer_guarded(api_key: str, model_name: str, exp_num: int, message: str) -> tuple:
    """Executes an async NeMo Guardrails evaluation inside an isolated worker thread."""
    log_buf = io.StringIO()
    log_handler = logging.StreamHandler(log_buf)
    log_handler.setLevel(logging.ERROR)
    nemo_log = logging.getLogger("nemoguardrails")

    def _worker():
        nemo_log.setLevel(logging.ERROR)
        nemo_log.addHandler(log_handler)
        try:
            llm   = ChatGroq(api_key=api_key, model=model_name, temperature=0)
            rails = build_control_plane_rails(llm)

            async def _coro():
                return await rails.generate_async(
                    messages=[{"role": "user", "content": message}]
                )

            return asyncio.run(_coro())
        finally:
            nemo_log.removeHandler(log_handler)
            nemo_log.setLevel(logging.ERROR)

    t0   = time.time()
    resp = _executor.submit(_worker).result(timeout=120)
    ms   = round((time.time() - t0) * 1000)

    if isinstance(resp, dict):
        content = resp.get("content") or resp.get("text") or resp.get("message") or (str(resp) if resp else "")
    elif isinstance(resp, str):
        content = resp
    else:
        content = str(resp) if resp else ""

    if not content or not str(content).strip():
        content = f"⚠️ [Empty response — raw: `{repr(resp)}`]"

    if "internal error" in str(content).lower():
        logs = log_buf.getvalue().strip()
        if logs:
            content = f"{content}\n\n---\n**NeMo error log:**\n```\n{logs}\n```"

    return str(content), ms
