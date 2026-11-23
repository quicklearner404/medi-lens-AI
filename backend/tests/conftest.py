"""Shared test setup: external APIs are replayed from recorded real responses."""

import json
from pathlib import Path

import httpx
import pytest

from medilens.druginfo import DrugInfoClient
from medilens.rxnorm import RXNAV, RxNormClient

FIXTURES = Path(__file__).parent / "fixtures"
RXNORM = json.loads((FIXTURES / "rxnorm.json").read_text())
DRUGINFO = json.loads((FIXTURES / "druginfo.json").read_text())


def _replay(request: httpx.Request) -> httpx.Response:
    query = request.url.query.decode()
    rxnorm_key = f"{request.url.path}?{query}"
    if request.url.host == "rxnav.nlm.nih.gov" and rxnorm_key in RXNORM:
        return httpx.Response(200, json=RXNORM[rxnorm_key])
    key = f"{request.url.host}{request.url.path}?{query}"
    if key in DRUGINFO:
        return httpx.Response(DRUGINFO[key]["status"], json=DRUGINFO[key]["body"])
    raise AssertionError(f"no recorded response for {request.url}; re-run the scripts/record_* scripts")


@pytest.fixture
def rxnorm():
    return RxNormClient(client=httpx.Client(base_url=RXNAV, transport=httpx.MockTransport(_replay)))


@pytest.fixture
def druginfo():
    return DrugInfoClient(client=httpx.Client(transport=httpx.MockTransport(_replay)))
