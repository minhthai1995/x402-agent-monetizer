"""x402 Agent Monetizer — FastAPI paywall + USDC-paying client for AI agents."""

from x402_agent_monetizer.client import Client
from x402_agent_monetizer.paywall import paywall

__version__ = "0.1.0"
__all__ = ["paywall", "Client"]
