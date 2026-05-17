"""Minimal FastAPI agent with two paywalled endpoints — run with uvicorn."""

from __future__ import annotations

import os

from fastapi import FastAPI

from x402_agent_monetizer import paywall

RECIPIENT = os.environ.get(
    "X402_RECIPIENT",
    "0x7aEDE9Bb3A0c28132643ED8e416e4728f03FC18f",  # demo wallet
)
NETWORK = os.environ.get("X402_NETWORK", "base-sepolia")

app = FastAPI(title="x402 agent demo")


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "x402 agent demo",
        "paid_routes": "/summarize ($0.01 USDC), /translate ($0.02 USDC)",
    }


@app.get("/summarize")
@paywall(price="0.01", network=NETWORK, recipient=RECIPIENT, description="One-paragraph summary")
def summarize(text: str) -> dict[str, str]:
    # A real implementation would call an LLM here.
    snippet = text[:80] + ("…" if len(text) > 80 else "")
    return {"summary": f"You sent {len(text)} chars. Preview: {snippet!r}"}


@app.get("/translate")
@paywall(price="0.02", network=NETWORK, recipient=RECIPIENT, description="EN→VN translation")
def translate(text: str) -> dict[str, str]:
    return {"translation": f"[VI] {text}"}
