import re
import os
import requests
from typing import Optional, List, Dict, Any
from nemoguardrails.actions import action


@action(is_system_action=True)
async def detect_pii_in_input(context: Optional[dict] = None) -> List[str]:
    """Scans user input for sensitive Personally Identifiable Information (PII) or API secrets."""
    user_message = context.get("user_message", "") if context else ""

    patterns = {
        "email":       r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        "phone":       r"\b(\+\d{1,2}\s?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b",
        "ssn":         r"\b\d{3}-\d{2}-\d{4}\b",
        "api_key":     r"(api[_\s-]?key|token|secret)[:\s]+[A-Za-z0-9_\-]{10,}",
        "credit_card": r"\b\d{4}[\s-]\d{4}[\s-]\d{4}[\s-]\d{4}\b",
    }
    found = [ptype for ptype, pat in patterns.items()
             if re.search(pat, user_message, re.IGNORECASE)]
    return found


@action(is_system_action=True)
async def classify_urgency(context: Optional[dict] = None) -> bool:
    """Detects whether a user message signals a critical Accenture enterprise outage or billing emergency."""
    msg = (context.get("user_message", "") if context else "").lower()
    urgent_keywords = [
        "outage", "down", "crash", "billing failure", "unauthorised charge",
        "api downtime", "emergency", "service down", "urgent", "p0", "p1",
    ]
    return any(kw in msg for kw in urgent_keywords)


@action(is_system_action=True)
async def sanitize_output(context: Optional[dict] = None) -> List[str]:
    """Intercepts and filters bot responses containing leaked credentials, computer code, or competitor endorsements."""
    bot_message = ""
    if context:
        bot_message = (
            context.get("bot_message")
            or context.get("response")
            or context.get("last_bot_message")
            or ""
        )

    sensitive_output_patterns = {
        "hardcoded_credential": r"(?i)(password|passwd|secret|api[_\-]?key|token)\s*[:=]\s*['\"]?\w{4,}",
        "code_block":           r"(```python|```bash|def\s+\w+|import\s+\w+)",
        "competitor_brand":     r"(?i)\b(deloitte|mckinsey|pwc|ey|kpmg|capgemini|tcs|cognizant|wipro|bain)\b",
        "financial_promise":    r"(?i)\b(guaranteed return|financial profit|investment advice)\b",
    }
    found = [ptype for ptype, pat in sensitive_output_patterns.items()
             if re.search(pat, bot_message)]
    return found


def calculate_risk_score(prompt: str, pii_detected: List[str], is_blocked: bool, is_urgent: bool) -> Dict[str, Any]:
    """
    Accenture Enterprise Risk Scoring Engine.
    Evaluates threat vector level (0.0 - 10.0 scale) based on prompt characteristics,
    PII detection, guardrail policy status, and brand safety signals.
    """
    score = 0.5  # base score
    threat_vectors = []

    if is_blocked:
        score += 4.5
        threat_vectors.append("Policy Refusal Triggered")

    if pii_detected:
        score += 3.0 * len(pii_detected)
        threat_vectors.append(f"PII Leak Vectors: {', '.join(pii_detected)}")

    prompt_lower = prompt.lower()
    jailbreak_signals = ["ignore", "dan", "developer mode", "unrestricted", "bypass", "override"]
    if any(sig in prompt_lower for sig in jailbreak_signals):
        score += 3.5
        threat_vectors.append("Prompt Injection Pattern")

    competitor_signals = ["deloitte", "mckinsey", "pwc", "ey", "kpmg", "capgemini", "tcs", "cognizant", "wipro", "bain"]
    if any(sig in prompt_lower for sig in competitor_signals):
        score += 3.0
        threat_vectors.append("Competitor Brand Query")

    code_signals = ["python", "code", "script", "scrape", "programming"]
    if any(sig in prompt_lower for sig in code_signals):
        score += 2.5
        threat_vectors.append("Code Generation Request")

    if is_urgent:
        threat_vectors.append("Platform Outage / Billing Emergency")

    score = min(10.0, max(0.0, score))

    if score >= 7.5:
        category = "CRITICAL"
        badge_color = "#E74C3C"
    elif score >= 4.5:
        category = "ELEVATED"
        badge_color = "#F39C12"
    else:
        category = "LOW RISK"
        badge_color = "#2ECC71"

    return {
        "score": round(score, 1),
        "category": category,
        "badge_color": badge_color,
        "threat_vectors": threat_vectors or ["None (Clean Input)"],
    }


def send_firebase_audit_log(event_data: Dict[str, Any]) -> bool:
    """Asynchronously dispatches audit record to Realtime Database endpoint if configured."""
    db_url = os.environ.get("FIREBASE_DATABASE_URL")
    if not db_url or not db_url.startswith("http"):
        return False

    try:
        url = f"{db_url.rstrip('/')}/audit_logs.json"
        response = requests.post(url, json=event_data, timeout=2)
        return response.status_code == 200
    except Exception:
        return False
