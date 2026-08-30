"""
Model catalogue definitions and default LLM configuration settings.
"""

GROQ_MODELS = {
    "openai/gpt-oss-120b": "OpenAI OSS · 120B — advanced reasoning",
    "openai/gpt-oss-20b":  "OpenAI OSS · 20B — fast & cost-effective",
}

GUARD_MODEL_DEFAULT = "openai/gpt-oss-120b"
CHAT_MODEL_DEFAULT  = "openai/gpt-oss-20b"

SYSTEM_PROMPT_RAW = "You are a helpful AI assistant for Accenture."
