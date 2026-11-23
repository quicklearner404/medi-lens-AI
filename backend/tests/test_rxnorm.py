"""RxNorm lookups, replayed from recorded real responses (no network)."""

import httpx
import pytest

from medilens.rxnorm import RXNAV, RxNormClient


@pytest.mark.parametrize(
    ("written", "generic"),
    [
        ("Panadol", "acetaminophen"),
        ("Glucophage 500mg", "metformin"),
        ("Xanax", "alprazolam"),
    ],
)
def test_brands_resolve_to_their_ingredient(rxnorm, written, generic):
    match = rxnorm.identify(written)

    assert match.concept_type == "BN"
    assert match.generic_name == generic


def test_combination_brand_lists_every_ingredient(rxnorm):
    match = rxnorm.identify("Augmentn")  # misspelt

    assert match.name == "Augmentin"
    assert {i.name for i in match.ingredients} == {"amoxicillin", "clavulanate"}


def test_misspelt_generic_is_corrected(rxnorm):
    match = rxnorm.identify("omeprazol")

    assert match.name == "omeprazole"
    assert match.concept_type == "IN"
    assert 0.8 <= match.similarity < 1.0


@pytest.mark.parametrize(
    ("written", "generic"),
    [("paracetamol", "acetaminophen"), ("salbutamol", "albuterol"),
     ("co-amoxiclav", "amoxicillin / clavulanate")],
)
def test_international_names_map_to_rxnorm_names(rxnorm, written, generic):
    match = rxnorm.identify(written)

    assert match.source == "synonym"
    assert match.generic_name == generic


@pytest.mark.parametrize(
    ("written", "generic"),
    [("Risek 20mg", "omeprazole"), ("Concor", "bisoprolol"), ("Disprin", "aspirin")],
)
def test_local_brands_use_the_pakistan_brand_list(rxnorm, written, generic):
    match = rxnorm.identify(written)

    assert match.source == "local-brand"
    assert match.generic_name == generic


def test_unknown_brand_is_not_guessed(rxnorm):
    # RxNorm's closest candidate for "Esita" is a cosmetic kit; it must be rejected.
    assert rxnorm.identify("Esita") is None


def test_empty_input(rxnorm):
    assert rxnorm.identify("  20mg ") is None
