import pytest

from medilens.directions import parse_directions


@pytest.mark.parametrize(
    ("line", "times_per_day"),
    [
        ("Tab Panadol 500mg OD", 1),
        ("Tab Augmentin 625mg BD", 2),
        ("Cap Amoxil 500mg TDS", 3),
        ("Tab Metformin 500mg tid", 3),
        ("Syp Brufen 5ml QID", 4),
        ("Tab Vitamin D once daily", 1),
    ],
)
def test_frequency_abbreviations(line, times_per_day):
    assert parse_directions(line).times_per_day == times_per_day


def test_dose_slots_morning_and_night():
    d = parse_directions("Tab Esita 10mg 1+0+1 x 5/7")

    assert d.times_per_day == 2
    assert d.slots == ["morning", "night"]
    assert d.dose == 1
    assert d.dose_unit == "tablet"


def test_dose_slots_with_dashes_and_halves():
    d = parse_directions("Tab Concor 2.5mg ½-0-0")

    assert d.slots == ["morning"]
    assert d.dose == 0.5


def test_unequal_slots_leave_dose_unset():
    d = parse_directions("Tab Glucophage 500mg 2+0+1")

    assert d.times_per_day == 2
    assert d.dose is None  # different amounts at different times; don't pick one


def test_strength_is_not_mistaken_for_dose():
    d = parse_directions("Cap Omeprazole 20mg 1 cap OD AC")

    assert d.strength == "20 mg"
    assert d.dose == 1 and d.dose_unit == "capsule"
    assert d.timing == "before meals"


def test_syrup_dose_in_ml():
    d = parse_directions("Syp Calpol 120mg/5ml 5 ml TDS")

    assert d.form == "syrup"
    assert d.dose == 5 and d.dose_unit == "ml"
    assert d.times_per_day == 3


def test_every_n_hours():
    d = parse_directions("Tab Paracetamol 1g q8h")

    assert d.every_hours == 8
    assert d.times_per_day == 3


@pytest.mark.parametrize(
    ("line", "days"),
    [
        ("Tab X 1+0+1 x 5/7", 5),
        ("Tab X BD x 2/52", 14),
        ("Tab X OD x 3/12", 90),
        ("Tab X OD for 10 days", 10),
        ("Tab X OD x 2 weeks", 14),
        ("Tab X OD x 1 month", 30),
        ("Tab X OD 7d", 7),
    ],
)
def test_durations(line, days):
    assert parse_directions(line).duration_days == days


def test_meal_timing_and_bedtime():
    assert parse_directions("Tab X BD PC").timing == "after meals"
    assert parse_directions("Tab X OD on empty stomach").timing == "before meals"

    bedtime = parse_directions("Tab Melatonin 3mg HS")
    assert bedtime.timing == "at bedtime"
    assert bedtime.times_per_day == 1


def test_as_needed_and_stat():
    assert parse_directions("Tab Panadol 500mg 1 tab SOS").as_needed
    assert parse_directions("Inj Voren 75mg stat").once_only


def test_unknown_text_stays_unparsed():
    d = parse_directions("Esita")

    assert d.times_per_day is None and d.dose is None and d.duration_days is None
    assert d.describe().startswith("Directions not recognised")


@pytest.mark.parametrize(
    ("line", "sentence"),
    [
        ("Tab Esita 10mg 1+0+1 x 5/7 PC",
         "1 tablet, twice a day (morning and night), after meals, for 5 days."),
        ("Cap Omeprazole 20mg 1 cap OD AC x 2/52",
         "1 capsule, once a day, before meals, for 2 weeks."),
        ("Syp Calpol 120mg/5ml 5 ml TDS x 3/7",
         "5 ml, three times a day, for 3 days."),
        ("Tab Panadol 500mg 2 tabs q6h SOS",
         "2 tablets, every 6 hours, only when needed."),
        ("Tab Concor 2.5mg ½+0+0 x 1 month",
         "Half a tablet, once a day (morning), for 1 month."),
    ],
)
def test_plain_english_description(line, sentence):
    assert parse_directions(line).describe() == sentence


def test_syrup_dose_without_printed_strength():
    # Found by the evaluation: a lone "5 ml" was taken as the strength, leaving no dose.
    d = parse_directions("Syp Brufen 5ml SOS")

    assert d.strength is None
    assert d.dose == 5 and d.dose_unit == "ml"
