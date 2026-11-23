# MediLens evaluation

Synthetic set: 174 medicines on 50 printed prescriptions (`evaluation/cases.jsonl`, ground truth written by hand).

| Metric | Value |
|---|---|
| Medicine lines detected | 99.4% |
| Extra (non-medicine) lines taken as medicines | 1 |
| Known names identified correctly (incl. typos) | 86.0% |
| **Wrong matches (dangerous)** | **2** |
| Medicines fully correct (identity + every direction field) | 71.8% |

## Identification by group

| Group | Correct | Abstained ("not recognised") | Wrong |
|---|---|---|---|
| invented name | 11 | 0 | 0 |
| known name | 126 | 14 | 2 |
| typo | 9 | 6 | 0 |
| unknown real brand | 0 | 5 | 0 |

For invented names, "correct" means they were reported as not recognised.

## Directions, per field

| Field | Accuracy |
|---|---|
| times_per_day | 91.1% |
| slots | 86.0% |
| dose | 86.8% |
| dose_unit | 86.8% |
| timing | 100.0% |
| duration_days | 99.4% |
| as_needed | 100.0% |

## Failures (74)

| Case | Medicine | Problem | Detail |
|---|---|---|---|
| rx01 | Esita | identification: abstained | expected ['escitalopram'] |
| rx01 | Zithromax | directions.dose | expected 5, got None / 'Syp. Zithromax 5 ml TDS AC x 3 weeks' |
| rx01 | Zithromax | directions.dose_unit | expected 'ml', got None / 'Syp. Zithromax 5 ml TDS AC x 3 weeks' |
| rx01 | metformin | not detected |  |
| rx01 | metformin three times a | extra item | 5. Cap metformin three times a day for 1 month |
| rx04 | co-amoxiclav | identification: wrong | expected ['amoxicillin', 'clavulanate'] |
| rx05 | amlodipine | directions.dose | expected 1, got None / 'Cap amlodipine 500mg one capsule at night x 1/12' |
| rx05 | amlodipine | directions.dose_unit | expected 'capsule', got None / 'Cap amlodipine 500mg one capsule at night x 1/12' |
| rx05 | Risek | directions.times_per_day | expected 3, got None / 'Tab Risek 10mg three times a day PC x 1/12' |
| rx05 | Calpl | identification: abstained | expected ['acetaminophen'] |
| rx05 | Amoxil | identification: abstained | expected ['amoxicillin'] |
| rx07 | Esita | identification: abstained | expected ['escitalopram'] |
| rx10 | Amoxil | identification: abstained | expected ['amoxicillin'] |
| rx10 | co-amoxiclav | identification: wrong | expected ['amoxicillin', 'clavulanate'] |
| rx10 | co-amoxiclav | directions.times_per_day | expected 2, got None / '4. TAB co-amoxiclav 10mg 1 tab morning and night PC for 1 month' |
| rx10 | co-amoxiclav | directions.slots | expected ['morning', 'night'], got [] / '4. TAB co-amoxiclav 10mg 1 tab morning and night PC for 1 month' |
| rx11 | Brufen | identification: abstained | expected ['ibuprofen'] |
| rx11 | paracetamol | directions.dose | expected 5, got None / '- Syp paracetamol 5ml SOS PC for 1 month' |
| rx11 | paracetamol | directions.dose_unit | expected 'ml', got None / '- Syp paracetamol 5ml SOS PC for 1 month' |
| rx14 | Dispriin | identification: abstained | expected ['aspirin'] |
| rx15 | Synthrroid | directions.times_per_day | expected 2, got None / '- Cap. Synthrroid 500mg 1 cap morning and night' |
| rx15 | Synthrroid | directions.slots | expected ['morning', 'night'], got [] / '- Cap. Synthrroid 500mg 1 cap morning and night' |
| rx15 | Brufen | identification: abstained | expected ['ibuprofen'] |
| rx18 | Nuvamax | directions.times_per_day | expected 3, got None / '1. Tablet Nuvamax 10mg three times a day AC x 1/12' |
| rx18 | Brufen | identification: abstained | expected ['ibuprofen'] |
| rx18 | Brufen | directions.dose | expected 5, got None / '- Syp. Brufen 5ml SOS on empty stomach for 10 days' |
| rx18 | Brufen | directions.dose_unit | expected 'ml', got None / '- Syp. Brufen 5ml SOS on empty stomach for 10 days' |
| rx19 | Esita | identification: abstained | expected ['escitalopram'] |
| rx19 | Esita | directions.dose | expected 1, got None / '1) Cap. Esita 500mg one capsule at night x 2/52' |
| rx19 | Esita | directions.dose_unit | expected 'capsule', got None / '1) Cap. Esita 500mg one capsule at night x 2/52' |
| rx21 | Nuvamax | directions.times_per_day | expected 3, got None / '1) Tablet Nuvamax 10mg' |
| rx21 | Nuvamax | directions.duration_days | expected 21, got None / '1) Tablet Nuvamax 10mg' |
| rx22 | Ponstan | identification: abstained | expected ['mefenamic acid'] |
| rx23 | Augmentin | directions.times_per_day | expected 3, got None / '3. Tab. Augmentin 250mg three times a day PC' |
| rx24 | Amoxil | identification: abstained | expected ['amoxicillin'] |
| rx27 | Synthroid | directions.times_per_day | expected 2, got None / 'Tablet Synthroid 500mg 1 tab morning and night PC for 1 month' |
| rx27 | Synthroid | directions.slots | expected ['morning', 'night'], got [] / 'Tablet Synthroid 500mg 1 tab morning and night PC for 1 month' |
| rx28 | Amoxil | identification: abstained | expected ['amoxicillin'] |
| rx29 | salbutamol | directions.dose | expected 1, got None / '- TAB salbutamol 500mg one tablet at night x 5/7' |
| rx29 | salbutamol | directions.dose_unit | expected 'tablet', got None / '- TAB salbutamol 500mg one tablet at night x 5/7' |
| rx30 | Augmentin | directions.dose | expected 1, got None / '3. Cap Augmentin 5mg one capsule at night for 1 month' |
| rx30 | Augmentin | directions.dose_unit | expected 'capsule', got None / '3. Cap Augmentin 5mg one capsule at night for 1 month' |
| rx31 | Panadol | directions.dose | expected 1, got None / '1. Cap Panadol 0.25mg one capsule at night x 3 weeks' |
| rx31 | Panadol | directions.dose_unit | expected 'capsule', got None / '1. Cap Panadol 0.25mg one capsule at night x 3 weeks' |
| rx33 | Norrvasc | directions.times_per_day | expected 2, got None / 'Tab Norrvasc 40mg 1 tab morning and night x 2/52' |
| rx33 | Norrvasc | directions.slots | expected ['morning', 'night'], got [] / 'Tab Norrvasc 40mg 1 tab morning and night x 2/52' |
| rx33 | Ponstaan | identification: abstained | expected ['mefenamic acid'] |
| rx34 | Arinac | identification: abstained | expected ['ibuprofen', 'pseudoephedrine'] |
| rx35 | Arinac | identification: abstained | expected ['ibuprofen', 'pseudoephedrine'] |
| rx35 | prednisolone | directions.times_per_day | expected 3, got None / 'Tab prednisolone 0.25mg three times a day for 10 days' |
| rx35 | Brufen | identification: abstained | expected ['ibuprofen'] |
| rx35 | Brufen | directions.dose | expected 10, got None / '- Syp. Brufen 10 ml BD x 1/12' |
| rx35 | Brufen | directions.dose_unit | expected 'ml', got None / '- Syp. Brufen 10 ml BD x 1/12' |
| rx35 | Ponstan | identification: abstained | expected ['mefenamic acid'] |
| rx36 | Brufen | identification: abstained | expected ['ibuprofen'] |
| rx36 | Disprin | directions.times_per_day | expected 3, got None / 'Tab. Disprin 5mg three times a day after meals x 3 weeks' |
| rx36 | Amoxil | identification: abstained | expected ['amoxicillin'] |
| rx38 | Brufen | identification: abstained | expected ['ibuprofen'] |
| rx41 | cetirizine | directions.dose | expected 5, got None / '2. Syp. cetirizine 5 ml TDS' |
| rx41 | cetirizine | directions.dose_unit | expected 'ml', got None / '2. Syp. cetirizine 5 ml TDS' |
| rx42 | Xanax | directions.dose | expected 1, got None / '3. Cap Xanax 20 mg one capsule at night x 7 days' |
| rx42 | Xanax | directions.dose_unit | expected 'capsule', got None / '3. Cap Xanax 20 mg one capsule at night x 7 days' |
| rx43 | Disprn | identification: abstained | expected ['aspirin'] |
| rx43 | Amxil | identification: abstained | expected ['amoxicillin'] |
| rx43 | Lexapro | directions.times_per_day | expected 2, got None / '3. Tab. Lexapro 10mg 1 tab morning and night on empty stomach x 2/52' |
| rx43 | Lexapro | directions.slots | expected ['morning', 'night'], got [] / '3. Tab. Lexapro 10mg 1 tab morning and night on empty stomach x 2/52' |
| rx44 | Glucophage | directions.times_per_day | expected 2, got None / '2. Cap Glucophage 1 cap morning and night for 10 days' |
| rx44 | Glucophage | directions.slots | expected ['morning', 'night'], got [] / '2. Cap Glucophage 1 cap morning and night for 10 days' |
| rx45 | Concor | directions.times_per_day | expected 2, got None / '3) Cap. Concor 40mg 1 cap morning and night after meals x 3 weeks' |
| rx45 | Concor | directions.slots | expected ['morning', 'night'], got [] / '3) Cap. Concor 40mg 1 cap morning and night after meals x 3 weeks' |
| rx46 | Augmentin | directions.dose | expected 1, got None / '3. Tab Augmentin 40mg one tablet at night' |
| rx46 | Augmentin | directions.dose_unit | expected 'tablet', got None / '3. Tab Augmentin 40mg one tablet at night' |
| rx46 | Cocor | identification: abstained | expected ['bisoprolol'] |
| rx49 | Brufen | identification: abstained | expected ['ibuprofen'] |
