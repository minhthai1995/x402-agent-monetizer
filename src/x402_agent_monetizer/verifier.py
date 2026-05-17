"""Thin async wrapper around the x402 facilitator's /verify endpoint."""

from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class VerificationResult:
    ok: bool
    reason: str
    receipt_id: str


class PaymentVerifier:
    """Posts the inbound X-PAYMENT header to the facilitator and parses its verdict."""

    def __init__(self, facilitator_url: str, timeout: float = 5.0) -> None:
        self._url = facilitator_url.rstrip("/") + "/verify"
        self._timeout = timeout

    async def verify(
        self,
        *,
        payment_header: str,
        expected_amount: str,
        expected_recipient: str,
        expected_network: str,
        expected_asset: str,
    ) -> VerificationResult:
        payload = {
            "payment": payment_header,
            "expects": {
                "scheme": "exact",
                "network": expected_network,
                "maxAmountRequired": expected_amount,
                "asset": expected_asset,
                "payTo": expected_recipient,
            },
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(self._url, json=payload)
        except httpx.HTTPError as exc:
            return VerificationResult(ok=False, reason=f"facilitator unreachable: {exc}", receipt_id="")

        if resp.status_code != 200:
            return VerificationResult(
                ok=False,
                reason=f"facilitator returned {resp.status_code}",
                receipt_id="",
            )
        data = resp.json()
        return VerificationResult(
            ok=bool(data.get("valid")),
            reason=data.get("reason", ""),
            receipt_id=data.get("receipt", ""),
        )
