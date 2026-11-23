"""Drug information from MedlinePlus and FDA labels, replayed from recorded responses."""

import json
from pathlib import Path

import httpx
import pytest

from medilens.druginfo import DrugInfoClient

FIXTURES = json.loads((Path(__file__).parent / "fixtures" / "druginfo.json").read_text())


def _replay(request: httpx.Request) -> httpx.Response:
    key = f"{request.url.host}{request.url.path}?{request.url.query.decode()}"
    if key not in FIXTURES:
        raise AssertionError(f"no recorded response for {key}; run scripts/record_druginfo_fixtures.py")
    return httpx.Response(FIXTURES[key]["status"], json=FIXTURES[key]["body"])


@pytest.fixture
def druginfo():
    return DrugInfoClient(client=httpx.Client(transport=httpx.MockTransport(_replay)))


def test_ssri_gets_patient_summary_and_stop_gradually_warning(druginfo):
    info = druginfo.lookup(["escitalopram"], "321988")

    assert info.found
    assert "SSRIs" in info.summary
    assert "depressive disorder" in info.used_for
    assert info.boxed_warning.startswith("SUICIDAL THOUGHTS")
    assert "reduce dosage gradually" in info.stop_gradually
    assert [s.name for s in info.sources] == ["MedlinePlus", "FDA drug label (DailyMed)"]
    assert info.sources[0].url == "https://medlineplus.gov/druginfo/meds/a603005.html"


def test_benzodiazepine_withdrawal_warning_is_about_the_patient(druginfo):
    info = druginfo.lookup(["alprazolam"], "596")

    assert info.stop_gradually.startswith("Abrupt discontinuation or rapid dosage reduction")
    assert "neonat" not in info.stop_gradually.lower()


def test_older_label_format_still_finds_abrupt_cessation_warning(druginfo):
    info = druginfo.lookup(["bisoprolol"], "19484")

    assert "Abrupt Cessation" in info.stop_gradually
    assert "hypertension" in info.used_for


def test_gradual_dose_increase_is_not_a_stopping_warning(druginfo):
    # Metformin's label talks about "gradual dose escalation" when starting.
    info = druginfo.lookup(["metformin"], "6809")

    assert info.found
    assert info.stop_gradually is None


def test_over_the_counter_label(druginfo):
    info = druginfo.lookup(["acetaminophen"], "161")

    assert "pain" in info.summary
    assert any(w.startswith("Liver warning") for w in info.key_warnings)
    assert info.stop_gradually is None


def test_combination_medicine_matches_a_label_with_both_ingredients(druginfo):
    info = druginfo.lookup(["amoxicillin", "clavulanate"], "19711")

    assert info.found
    assert "clavulanate" in info.used_for.lower()


def test_unknown_medicine_returns_nothing_rather_than_a_guess(druginfo):
    info = druginfo.lookup(["notarealmedicine"])

    assert not info.found
    assert info.sources == []
