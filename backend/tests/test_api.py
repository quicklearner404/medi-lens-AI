import httpx
import pytest
from fastapi.testclient import TestClient

from medilens.analysis import PrescriptionAnalyzer
from medilens.api import create_app
from medilens.rxnorm import RXNAV, RxNormClient

PRESCRIPTION = """\
Dr. Ayesha Khan, City Clinic Lahore
Patient: Ali Raza   Age 34   Date 12/11/2026
Rx
1. Tab Esita 10mg 1+0+0 x 1 month
2. Tab Xanax 0.25mg 0+0+1 x 2/52
3. Tab Concor 5mg OD
4. Tab Panadol 500mg 2 tabs SOS
5. Tab Glucophage 500mg 1+0+1 PC
"""


@pytest.fixture
def client(rxnorm, druginfo):
    return TestClient(create_app(PrescriptionAnalyzer(rxnorm=rxnorm, druginfo=druginfo)))


@pytest.fixture
def cards(client):
    response = client.post("/analyze", json={"text": PRESCRIPTION})
    assert response.status_code == 200
    return {c["written_name"]: c for c in response.json()["medicines"]}


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_one_card_per_medicine_in_order(client):
    names = [c["written_name"] for c in client.post("/analyze", json={"text": PRESCRIPTION}).json()["medicines"]]

    assert names == ["Esita", "Xanax", "Concor", "Panadol", "Glucophage"]


def test_known_brand_card_has_directions_information_and_sources(cards):
    xanax = cards["Xanax"]

    assert xanax["recognised"] and xanax["generic_name"] == "alprazolam"
    assert xanax["directions"]["summary"] == "1 tablet, once a day (night), for 2 weeks."
    assert "anxiety" in xanax["info"]["summary"]
    assert xanax["info"]["stop_gradually"].startswith("Abrupt discontinuation")
    assert {s["name"] for s in xanax["info"]["sources"]} == {"MedlinePlus", "FDA drug label (DailyMed)"}
    assert xanax["needs_review"] == []


def test_local_brand_is_explained_with_its_stop_warning(cards):
    concor = cards["Concor"]

    assert concor["generic_name"] == "bisoprolol" and concor["match_source"] == "local-brand"
    assert "Abrupt Cessation" in concor["info"]["stop_gradually"]


def test_medicines_that_can_be_stopped_have_no_stop_warning(cards):
    assert cards["Panadol"]["info"]["stop_gradually"] is None
    assert cards["Glucophage"]["info"]["stop_gradually"] is None


def test_unrecognised_brand_asks_the_user_instead_of_guessing(cards):
    esita = cards["Esita"]

    assert not esita["recognised"]
    assert esita["info"] is None
    assert "was not recognised" in esita["needs_review"][0]
    # the directions are still explained, since they don't depend on the medicine
    assert esita["directions"]["summary"] == "1 tablet, once a day (morning), for 1 month."


def test_every_response_carries_the_disclaimer(client):
    body = client.post("/analyze", json={"text": "Tab Panadol 500mg SOS"}).json()

    assert "not medical advice" in body["disclaimer"]


def test_text_without_medicines_returns_an_empty_list(client):
    assert client.post("/analyze", json={"text": "Follow up after 2 weeks"}).json()["medicines"] == []


def test_empty_and_oversized_input_is_rejected(client):
    assert client.post("/analyze", json={"text": ""}).status_code == 422
    assert client.post("/analyze", json={"text": "x" * 5001}).status_code == 422


def test_unreachable_database_is_reported_on_the_card_not_as_an_error(druginfo):
    def offline(request):
        raise httpx.ConnectError("network down", request=request)

    rxnorm = RxNormClient(client=httpx.Client(base_url=RXNAV, transport=httpx.MockTransport(offline)))
    client = TestClient(create_app(PrescriptionAnalyzer(rxnorm=rxnorm, druginfo=druginfo)))

    response = client.post("/analyze", json={"text": "Tab Panadol 500mg SOS"})

    assert response.status_code == 200
    card = response.json()["medicines"][0]
    assert not card["recognised"]
    assert "could not be reached" in card["needs_review"][0]
