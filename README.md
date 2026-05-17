# x402 Agent Monetizer

Monetize FastAPI AI agent endpoints with the [x402 payment protocol](https://www.x402.org/) — get paid in USDC per request, no signups, no API keys, no human in the loop.

> **Found this useful?** [☕ Buy me a coffee](https://ko-fi.com/fixabug95) · [💜 GitHub Sponsors](https://github.com/sponsors/minhthai1995) · USDC tip: `0x7aEDE9Bb3A0c28132643ED8e416e4728f03FC18f` (Base)

## What this is

Drop-in FastAPI middleware that puts a USDC paywall in front of your agent endpoints. When a client hits a paid route without payment, the server returns `HTTP 402 Payment Required` with the price + recipient address. The client (human or AI) signs a USDC transfer over EIP-3009, retries the request, and gets the response.

Built for Python AI agents on Base. Uses [`x402` v2.10+](https://pypi.org/project/x402/) and the Coinbase-hosted facilitator (1,000 free tx/month).

## Why

The agent economy needs micro-payments, not subscriptions. x402 lets agents transact in under a second for fractions of a cent. This repo is the FastAPI-flavored shortest path.

## Install

```bash
pip install -e ".[fastapi]"
```

Requires Python 3.10+.

## Quick start (server)

```python
from fastapi import FastAPI
from x402_agent_monetizer import paywall

app = FastAPI()

# Paywalled endpoint — caller must pay $0.05 USDC on Base before getting the response
@app.get("/summarize")
@paywall(price="0.05", network="base", recipient="0x7aEDE9Bb3A0c28132643ED8e416e4728f03FC18f")
def summarize(text: str):
    # your agent logic here
    return {"summary": f"<summary of {len(text)} chars>"}
```

Run:

```bash
uvicorn examples.fastapi_agent:app --reload
```

## Quick start (client)

```python
from x402_agent_monetizer import Client

client = Client(private_key="0x...", network="base")
resp = client.get("http://localhost:8000/summarize", params={"text": "hello"})
print(resp.json())  # auto-paid + retried
```

See `examples/agent_client.py` for a full agent loop.

## Supported networks

| Network       | Status |
|---------------|--------|
| Base mainnet  | ✅ |
| Base Sepolia  | ✅ (testnet) |
| Polygon       | ✅ |
| Arbitrum      | ✅ |
| Solana        | ✅ |

Pricing dict accepts `USDC`, `EURC`, or any ERC-20 with EIP-3009 / Permit2.

## Repo layout

```
src/x402_agent_monetizer/   # paywall decorator + Client wrapper
examples/                   # runnable end-to-end demos
tests/                      # pytest smoke tests
```

## Roadmap

- [x] FastAPI paywall decorator
- [x] Sync + async client wrappers
- [ ] Flask + Starlette middleware
- [ ] Replay-attack protection
- [ ] Per-caller rate limits + receipts
- [ ] Coinbase AgentKit integration

## License

MIT — see [LICENSE](LICENSE).
