"""FastAPI-compatible `@paywall` decorator backed by the x402 protocol."""

from __future__ import annotations

import functools
import inspect
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from x402_agent_monetizer.verifier import PaymentVerifier

DEFAULT_FACILITATOR = "https://x402.org/facilitator"
DEFAULT_NETWORK = "base"
DEFAULT_ASSET = "USDC"


@dataclass(frozen=True)
class PaywallConfig:
    price: str
    network: str
    recipient: str
    asset: str
    facilitator: str
    description: str | None


def _payment_required_response(cfg: PaywallConfig, route: str) -> JSONResponse:
    """Build the canonical HTTP 402 body advertising what the client must pay."""
    body = {
        "x402Version": 1,
        "accepts": [
            {
                "scheme": "exact",
                "network": cfg.network,
                "maxAmountRequired": cfg.price,
                "asset": cfg.asset,
                "payTo": cfg.recipient,
                "resource": route,
                "description": cfg.description or "",
                "facilitator": cfg.facilitator,
            }
        ],
    }
    return JSONResponse(status_code=402, content=body)


def paywall(
    price: str,
    *,
    network: str = DEFAULT_NETWORK,
    recipient: str,
    asset: str = DEFAULT_ASSET,
    facilitator: str = DEFAULT_FACILITATOR,
    description: str | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator that gates a FastAPI endpoint behind an x402 USDC payment.

    The wrapped function is invoked only after the inbound request's
    `X-PAYMENT` header verifies against the configured facilitator.
    """
    cfg = PaywallConfig(
        price=price,
        network=network,
        recipient=recipient,
        asset=asset,
        facilitator=facilitator,
        description=description,
    )
    verifier = PaymentVerifier(facilitator_url=facilitator)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        is_async = inspect.iscoroutinefunction(func)

        @functools.wraps(func)
        async def wrapper(*args: Any, request: Request, **kwargs: Any) -> Any:
            payment_header = request.headers.get("X-PAYMENT")
            if not payment_header:
                return _payment_required_response(cfg, str(request.url.path))

            verified = await verifier.verify(
                payment_header=payment_header,
                expected_amount=cfg.price,
                expected_recipient=cfg.recipient,
                expected_network=cfg.network,
                expected_asset=cfg.asset,
            )
            if not verified.ok:
                raise HTTPException(status_code=402, detail=verified.reason)

            result = func(*args, **kwargs) if not is_async else await func(*args, **kwargs)
            response = (
                JSONResponse(content=result) if not isinstance(result, JSONResponse) else result
            )
            response.headers["X-PAYMENT-RECEIPT"] = verified.receipt_id
            return response

        # Preserve FastAPI's ability to inject `request: Request` automatically.
        sig = inspect.signature(func)
        params = list(sig.parameters.values())
        if not any(p.annotation is Request for p in params):
            params.append(
                inspect.Parameter(
                    "request",
                    inspect.Parameter.KEYWORD_ONLY,
                    annotation=Request,
                )
            )
            wrapper.__signature__ = sig.replace(parameters=params)  # type: ignore[attr-defined]
        return wrapper

    return decorator
