from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

PRICING_CURRENCY = "USD"

# Placeholder registry: keep centralized so values are easy to update.
# Costs are USD per 1M tokens.
MODEL_PRICING = {
    ("openai", "gpt-4.1"): {"input_cost_per_1m_tokens": Decimal("10.00"), "output_cost_per_1m_tokens": Decimal("30.00"), "currency": PRICING_CURRENCY},
    ("openai", "gpt-4.1-mini"): {"input_cost_per_1m_tokens": Decimal("0.40"), "output_cost_per_1m_tokens": Decimal("1.60"), "currency": PRICING_CURRENCY},
    ("openai", "gpt-4o-mini"): {"input_cost_per_1m_tokens": Decimal("0.15"), "output_cost_per_1m_tokens": Decimal("0.60"), "currency": PRICING_CURRENCY},
    ("gemini", "gemini-1.5-pro"): {"input_cost_per_1m_tokens": Decimal("3.50"), "output_cost_per_1m_tokens": Decimal("10.50"), "currency": PRICING_CURRENCY},
    ("gemini", "gemini-1.5-flash"): {"input_cost_per_1m_tokens": Decimal("0.35"), "output_cost_per_1m_tokens": Decimal("0.70"), "currency": PRICING_CURRENCY},
}


def estimate_llm_cost(provider: str | None, model: str | None, input_tokens: int | None, output_tokens: int | None) -> dict:
    pricing = MODEL_PRICING.get(((provider or "").lower(), model or ""))
    if not pricing or input_tokens is None or output_tokens is None:
        return {"estimated_cost_usd": None, "currency": PRICING_CURRENCY, "pricing_known": False}

    input_cost = (Decimal(input_tokens) / Decimal(1_000_000)) * pricing["input_cost_per_1m_tokens"]
    output_cost = (Decimal(output_tokens) / Decimal(1_000_000)) * pricing["output_cost_per_1m_tokens"]
    total = (input_cost + output_cost).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
    return {"estimated_cost_usd": total, "currency": pricing["currency"], "pricing_known": True}
