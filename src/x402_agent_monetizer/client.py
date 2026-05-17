"""Drop-in HTTP client that auto-pays x402 paywalls in USDC."""

from __future__ import annotations

from typing import Any

import httpx

DEFAULT_FACILITATOR = "https://x402.org/facilitator"


class Client:
    """Sends HTTP requests; if a 402 comes back, sign+pay+retry once."""

    def __init__(
        self,
        private_key: str,
        *,
        network: str = "base",
        facilitator: str = DEFAULT_FACILITATOR,
        timeout: float = 30.0,
    ) -> None:
        self._private_key = private_key
        self._network = network
        self._facilitator = facilitator
        self._http = httpx.Client(timeout=timeout)

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return self._request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return self._request("POST", url, **kwargs)

    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        resp = self._http.request(method, url, **kwargs)
        if resp.status_code != 402:
            return resp

        challenge = resp.json()
        accept = challenge["accepts"][0]
        if accept["network"] != self._network:
            raise RuntimeError(
                f"server demands payment on {accept['network']}, "
                f"client configured for {self._network}"
            )
        payment_header = self._sign_payment(accept)
        headers = dict(kwargs.pop("headers", {}) or {})
        headers["X-PAYMENT"] = payment_header
        return self._http.request(method, url, headers=headers, **kwargs)

    def _sign_payment(self, accept: dict[str, Any]) -> str:
        """Produce an X-PAYMENT header value via the x402 SDK.

        Kept thin so a unit test can monkeypatch this method without touching
        the chain.
        """
        from x402 import x402Client
        from x402.mechanisms.evm.exact import ExactEvmScheme
        from eth_account import Account

        signer = Account.from_key(self._private_key)
        client = x402Client()
        client.register("eip155:*", ExactEvmScheme(signer=signer))
        # x402 SDK returns the payment payload; we serialize to the header form.
        payload = client.create_payment_payload_sync(accept)
        return payload.to_header()

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "Client":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
