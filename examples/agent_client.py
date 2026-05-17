"""Example agent loop — calls a paid endpoint, auto-pays, prints the result."""

from __future__ import annotations

import os
import sys

from x402_agent_monetizer import Client


def main() -> int:
    private_key = os.environ.get("AGENT_PRIVATE_KEY")
    if not private_key:
        print("ERROR: set AGENT_PRIVATE_KEY (a Base-sepolia funded EOA).", file=sys.stderr)
        return 2

    target = os.environ.get("AGENT_TARGET", "http://localhost:8000/summarize")
    with Client(private_key=private_key, network=os.environ.get("X402_NETWORK", "base-sepolia")) as c:
        resp = c.get(target, params={"text": "x402 monetizes AI agent endpoints with USDC."})
        print("status:", resp.status_code)
        print("body  :", resp.json())
        receipt = resp.headers.get("X-PAYMENT-RECEIPT")
        if receipt:
            print("paid receipt:", receipt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
