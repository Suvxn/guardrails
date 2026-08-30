# Graphviz DOT strings for guardrail flow pipeline diagrams.
# Rendered via st.graphviz_chart() in Streamlit.

_COMMON = """
  node [shape=box style=filled fontname="Arial" fontsize=12]
  edge [fontname="Arial" fontsize=10]
"""

_USER = 'User [label="User\\nMessage" shape=oval fillcolor="#D6EAF8"]'
_BOT  = 'Bot  [label="Bot\\nResponse"  shape=oval fillcolor="#D6EAF8"]'

DIAGRAMS = {

    1: f"""digraph {{
  rankdir=LR
  {_COMMON}
  {_USER}
  LLM [label="Raw LLM\\n(No Guardrails)" fillcolor="#FADBD8"]
  {_BOT}

  User -> LLM [label=" no filtering "]
  LLM  -> Bot
}}""",

    2: f"""digraph {{
  rankdir=LR
  {_COMMON}
  {_USER}
  Intent [label="Intent Check\\n(LLM Call 1)" fillcolor="#FEF9E7"]
  Block  [label="Refuse:\\nOff-Topic / Competitor" fillcolor="#FADBD8"]
  LLM    [label="Accenture LLM\\n(LLM Call 2)" fillcolor="#D5F5E3"]
  {_BOT}

  User   -> Intent
  Intent -> Block [label="off-topic / competitor"]
  Intent -> LLM   [label="Accenture query"]
  Block  -> Bot
  LLM    -> Bot
}}""",

    3: f"""digraph {{
  rankdir=LR
  {_COMMON}
  {_USER}
  Intent  [label="Intent Check\\n(LLM Call 1)" fillcolor="#FEF9E7"]
  BkOT    [label="Refuse:\\nOff-Topic"   fillcolor="#FADBD8"]
  BkJB    [label="Refuse:\\nJailbreak / Code" fillcolor="#FADBD8"]
  LLM     [label="Accenture LLM\\n(LLM Call 2)" fillcolor="#D5F5E3"]
  {_BOT}

  User   -> Intent
  Intent -> BkOT [label="off-topic"]
  Intent -> BkJB [label="jailbreak / code"]
  Intent -> LLM  [label="Accenture query"]
  BkOT   -> Bot
  BkJB   -> Bot
  LLM    -> Bot
}}""",

    4: f"""digraph {{
  rankdir=LR
  {_COMMON}
  {_USER}
  Intent [label="Intent Check\\n(LLM Call 1)"  fillcolor="#FEF9E7"]
  BkOT   [label="Refuse:\\nOff-Topic"          fillcolor="#FADBD8"]
  BkJB   [label="Refuse:\\nJailbreak / Code"   fillcolor="#FADBD8"]
  BkST   [label="Refuse:\\nCompetitor / Financial" fillcolor="#FADBD8"]
  LLM    [label="Accenture LLM\\n(LLM Call 2)"   fillcolor="#D5F5E3"]
  {_BOT}

  User   -> Intent
  Intent -> BkOT [label="off-topic"]
  Intent -> BkJB [label="jailbreak / code"]
  Intent -> BkST [label="competitor / financial"]
  Intent -> LLM  [label="allowed Accenture query"]
  BkOT   -> Bot
  BkJB   -> Bot
  BkST   -> Bot
  LLM    -> Bot
}}""",

    5: f"""digraph {{
  rankdir=LR
  {_COMMON}
  {_USER}
  Intent  [label="Intent Check\\n(LLM Call 1)"     fillcolor="#FEF9E7"]
  BkOT    [label="Refuse:\\nOff-Topic"             fillcolor="#FADBD8"]
  BkJB    [label="Refuse:\\nJailbreak / Code"      fillcolor="#FADBD8"]
  BkST    [label="Refuse:\\nCompetitor / Financial" fillcolor="#FADBD8"]
  Dialog  [label="Scripted Dialog\\ngreeting / capabilities / bye" fillcolor="#E8DAEF"]
  LLM     [label="Accenture LLM\\n(LLM Call 2)"      fillcolor="#D5F5E3"]
  {_BOT}

  User   -> Intent
  Intent -> BkOT   [label="off-topic"]
  Intent -> BkJB   [label="jailbreak / code"]
  Intent -> BkST   [label="competitor / financial"]
  Intent -> Dialog [label="dialog intent"]
  Intent -> LLM    [label="Accenture query"]
  BkOT   -> Bot
  BkJB   -> Bot
  BkST   -> Bot
  Dialog -> Bot [label="0 LLM tokens"]
  LLM    -> Bot
}}""",

    6: f"""digraph {{
  rankdir=LR
  {_COMMON}
  {_USER}
  PII     [label="PII Detector\\n(Python Action)\\nsystematic — every msg"  fillcolor="#FDEBD0"]
  Urgency [label="Urgency Detector\\n(Python Action)\\nsystematic — every msg" fillcolor="#FDEBD0"]
  BkPII   [label="Block:\\nPII Found" fillcolor="#FADBD8"]
  Warn    [label="Warn: Emergency!\\nthen continue" fillcolor="#FEF9E7"]
  Intent  [label="Intent Check\\n(LLM Call 1)"  fillcolor="#FEF9E7"]
  LLM     [label="Accenture LLM\\n(LLM Call 2)"   fillcolor="#D5F5E3"]
  {_BOT}

  User    -> PII     [label="every msg"]
  PII     -> BkPII   [label="PII found → stop"]
  PII     -> Urgency [label="clean"]
  Urgency -> Warn    [label="outage / billing emergency"]
  Urgency -> Intent  [label="normal"]
  Warn    -> Intent  [label="continue"]
  Intent  -> LLM     [label="allowed"]
  BkPII   -> Bot
  Intent  -> Bot     [label="rail fired"]
  LLM     -> Bot
}}""",

    7: f"""digraph {{
  rankdir=LR
  {_COMMON}
  {_USER}
  Intent   [label="Intent Check\\n(LLM Call 1)"           fillcolor="#FEF9E7"]
  LLM      [label="Accenture LLM\\n(LLM Call 2)"       fillcolor="#D5F5E3"]
  OutRail  [label="Output Sanitizer\\n(Python Action)\\nsystematic — every response" fillcolor="#FDEBD0"]
  Withheld [label="Response\\nWithheld"                   fillcolor="#FADBD8"]
  {_BOT}

  User    -> Intent
  Intent  -> LLM     [label="allowed"]
  LLM     -> OutRail [label="every response"]
  OutRail -> Withheld [label="code / credential /\\ncompetitor leak found"]
  OutRail -> Bot      [label="clean"]
  Withheld -> Bot     [label="safe message"]
}}""",

    8: f"""digraph {{
  rankdir=LR
  {_COMMON}
  {_USER}
  PII      [label="PII Detector\\n(Python Action)"            fillcolor="#FDEBD0"]
  Urgency  [label="Urgency Detector\\n(Python Action)"        fillcolor="#FDEBD0"]
  Intent   [label="Multi-Rail Intent Check\\n(LLM Call 1)"      fillcolor="#FEF9E7"]
  Dialog   [label="Scripted Dialog\\n(0 LLM Tokens)"          fillcolor="#E8DAEF"]
  LLM      [label="Accenture LLM Answer\\n(LLM Call 2)"      fillcolor="#D5F5E3"]
  OutRail  [label="Output Sanitizer\\n(Python Action)"        fillcolor="#FDEBD0"]
  Block    [label="Policy Blocked /\\nWithheld"               fillcolor="#FADBD8"]
  {_BOT}

  User     -> PII
  PII      -> Block   [label="PII found"]
  PII      -> Urgency [label="clean"]
  Urgency  -> Intent  [label="scanned"]
  Intent   -> Block   [label="off-topic / jailbreak / competitor"]
  Intent   -> Dialog  [label="greeting / help"]
  Intent   -> LLM     [label="allowed Accenture query"]
  LLM      -> OutRail
  OutRail  -> Block   [label="leak found"]
  OutRail  -> Bot     [label="clean response"]
  Dialog   -> Bot     [label="scripted reply"]
  Block    -> Bot
}}""",
}


def get_diagram(exp_num: int) -> str:
    """Returns Graphviz DOT representation for experiment pipeline."""
    return DIAGRAMS.get(exp_num, "")
