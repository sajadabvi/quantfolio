"""
Synthesis layer. Two backends:
  1. rule_based_brief() — always available. Deterministic, no network.
  2. llm_brief() — calls the Claude API when ANTHROPIC_API_KEY is set.

Output is a short multi-line string. Never frames as "buy/sell" — language is
"this changes your thesis on X because Y."
"""

from __future__ import annotations

import os
from typing import Optional


DEFAULT_MODEL = "claude-sonnet-4-6"


def _format_weight(w: Optional[float]) -> str:
    if not isinstance(w, (int, float)) or w <= 0:
        return "no direct exposure"
    return f"{w*100:.1f}% of portfolio"


def rule_based_brief(signals: list, limit: int = 3) -> str:
    """
    Deterministic template: one bullet per signal, phrased as a thesis note.
    Matches the 'this changes your thesis on X because Y' framing.
    """
    if not signals:
        return "No signals above threshold. No action-shaping news in today's fetch."

    top = signals[:limit]
    bullets = []
    for s in top:
        d = s.as_dict() if hasattr(s, "as_dict") else s
        sym = d.get("symbol") or "—"
        weight_s = _format_weight(d.get("portfolio_weight"))
        title = d.get("title", "").strip()
        hits = d.get("components", {}).get("materiality_hits") or []
        angle = _angle_for_hits(hits, title)
        bullets.append(f"• {sym} ({weight_s}): {title}. {angle}")
    return "\n".join(bullets)


def _angle_for_hits(hits: list[str], title: str) -> str:
    """Pick an angle phrase based on which materiality keywords matched."""
    hits_low = [h.lower() for h in hits]
    if "halt" in hits_low or "halted" in title.lower():
        return "Trading halt — positioning frozen until reopen; re-evaluate thesis on resumption."
    if any(h in hits_low for h in ("m&a", "acquire", "acquisition", "merger")):
        return "Changes the thesis from organic-growth story to integration-risk story."
    if "earnings" in hits_low and "guidance" in hits_low:
        return "Both print and forward guidance moved — re-anchor your estimate range."
    if "earnings" in hits_low:
        return "Thesis check: does the print confirm or contradict your growth assumption?"
    if "guidance" in hits_low:
        return "Management updated the forward — your outer-year model should move with it."
    if "downgrade" in hits_low:
        return "Sell-side conviction shifted — check whether the stated reason applies to your thesis."
    if "upgrade" in hits_low:
        return "Sell-side now on-side — confirm whether the catalyst matches your own."
    if "fda" in hits_low or "approval" in hits_low:
        return "Regulatory milestone reshapes the probability tree on this name."
    if "lawsuit" in hits_low or "subpoena" in hits_low or "probe" in hits_low:
        return "Legal/regulatory tail added — incorporate into downside case."
    if "bankruptcy" in hits_low:
        return "Capital-structure distress — re-examine recovery assumptions."
    if "recall" in hits_low:
        return "Unit-economics hit plus reputational tail — reassess margin trajectory."
    if "buyback" in hits_low or "dividend" in hits_low:
        return "Capital-return signal — factor into total-return expectation, not valuation."
    if "insider" in hits_low:
        return "Insider signal — weigh alongside your qualitative read of management conviction."
    if "resign" in hits_low or "layoffs" in hits_low:
        return "People/org signal — watch for strategy discontinuity."
    return "Worth a read — may shift your read on this name."


def llm_brief(
    signals: list,
    portfolio_weights: dict,
    limit: int = 3,
    model: str = DEFAULT_MODEL,
) -> Optional[str]:
    """
    Ask the Claude API for a 3-bullet brief. Returns None if the SDK isn't
    available or ANTHROPIC_API_KEY is not set — caller should fall back.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        from anthropic import Anthropic
    except ImportError:
        return None

    top = signals[:limit]
    if not top:
        return "No signals above threshold."

    headlines_text = "\n".join(
        f"- [{(s.as_dict() if hasattr(s,'as_dict') else s).get('symbol','—')} "
        f"weight={_format_weight((s.as_dict() if hasattr(s,'as_dict') else s).get('portfolio_weight'))}] "
        f"{(s.as_dict() if hasattr(s,'as_dict') else s).get('title','')} "
        f"({(s.as_dict() if hasattr(s,'as_dict') else s).get('domain','')})"
        for s in top
    )
    weights_text = "\n".join(f"  {sym}: {w*100:.1f}%" for sym, w in sorted(
        portfolio_weights.items(), key=lambda kv: -kv[1]
    ))

    system = (
        "You are a concise portfolio analyst. Produce exactly N bullet points, "
        "one per headline given. Each bullet names the ticker, the event, the "
        "user's exposure, and the decision-relevant angle. Frame as "
        "'this changes your thesis on X because Y'. NEVER tell the user to buy "
        "or sell. Keep each bullet to one or two sentences."
    )
    user = (
        f"User's portfolio weights:\n{weights_text}\n\n"
        f"Top {len(top)} scored headlines:\n{headlines_text}\n\n"
        f"Write {len(top)} bullets."
    )

    try:
        client = Anthropic(api_key=api_key)
        resp = client.messages.create(
            model=model,
            max_tokens=500,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        parts = []
        for block in resp.content:
            if getattr(block, "type", None) == "text":
                parts.append(block.text)
        text = "\n".join(parts).strip()
        return text or None
    except Exception:
        return None


def brief_text(
    signals: list,
    portfolio_weights: dict,
    limit: int = 3,
    use_llm: bool = True,
) -> tuple[str, str]:
    """Return (text, backend_used)."""
    if use_llm:
        out = llm_brief(signals, portfolio_weights, limit=limit)
        if out:
            return out, "claude"
    return rule_based_brief(signals, limit=limit), "rule-based"
