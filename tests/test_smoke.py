"""Smoke tests — verify the 402 challenge is returned when no payment is presented."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def app():
    from examples.fastapi_agent import app as fastapi_app
    return fastapi_app


def test_root_is_open(app):
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "paid_routes" in resp.json()


def test_paid_route_returns_402_without_payment(app):
    client = TestClient(app)
    resp = client.get("/summarize", params={"text": "hi"})
    assert resp.status_code == 402
    body = resp.json()
    assert body["x402Version"] == 1
    accept = body["accepts"][0]
    assert accept["maxAmountRequired"] == "0.01"
    assert accept["asset"] == "USDC"
    assert accept["payTo"].startswith("0x")


def test_translate_advertises_higher_price(app):
    client = TestClient(app)
    resp = client.get("/translate", params={"text": "hi"})
    assert resp.status_code == 402
    assert resp.json()["accepts"][0]["maxAmountRequired"] == "0.02"
