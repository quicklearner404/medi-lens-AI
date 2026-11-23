from medilens.prescription import read_prescription

PRESCRIPTION = """\
Dr. Ayesha Khan
MBBS, FCPS (Psychiatry)
City Clinic, Lahore   Ph: 042-0000000
Patient: Ali Raza     Age: 34 Y    Date: 12/11/2026
Diagnosis: Generalised anxiety disorder

Rx
1. Tab. Esita 10mg 1+0+0 x 1 month
2. Tab Xanax 0.25mg
   0+0+1 x 2/52 at night
3) Cap. Risek 20 mg OD AC x 2/52
4. Syp. Calpol 120mg/5ml 5 ml TDS SOS

Follow up after 4 weeks
Signature
"""


def test_reads_only_the_medicine_lines():
    items = read_prescription(PRESCRIPTION)

    assert [i.written_name for i in items] == ["Esita", "Xanax", "Risek", "Calpol"]


def test_directions_on_the_next_line_are_attached():
    xanax = read_prescription(PRESCRIPTION)[1]

    assert xanax.directions.slots == ["night"]
    assert xanax.directions.duration_days == 14


def test_each_item_keeps_its_parsed_directions():
    esita, _, risek, calpol = read_prescription(PRESCRIPTION)

    assert esita.directions.describe() == "1 tablet, once a day (morning), for 1 month."
    assert risek.directions.timing == "before meals"
    assert calpol.directions.dose == 5 and calpol.directions.as_needed


def test_multi_word_and_alphanumeric_names():
    items = read_prescription("Tab Vitamin D3 50000 IU once weekly\nCap Omega 3 1 cap OD")

    assert [i.written_name for i in items] == ["Vitamin D3", "Omega"]


def test_header_lines_with_numbers_are_ignored():
    text = "Patient: Sara  Age 8\nDate 1/2/2026\nBP 120/80\nTab Brufen 200mg TDS PC"

    assert [i.written_name for i in read_prescription(text)] == ["Brufen"]


def test_empty_text():
    assert read_prescription("") == []
