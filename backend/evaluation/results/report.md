# MediLens evaluation

Synthetic set: 174 medicines on 50 printed prescriptions (`evaluation/cases.jsonl`, ground truth written by hand).

| Metric | Value |
|---|---|
| Medicine lines detected | 100.0% |
| Extra (non-medicine) lines taken as medicines | 0 |
| Known names identified correctly (incl. typos) | 96.2% |
| **Wrong matches (dangerous)** | **0** |
| Medicines fully correct (identity + every direction field) | 93.7% |

## Identification by group

| Group | Correct | Abstained ("not recognised") | Wrong |
|---|---|---|---|
| invented name | 11 | 0 | 0 |
| known name | 143 | 0 | 0 |
| typo | 9 | 6 | 0 |
| unknown real brand | 0 | 5 | 0 |

For invented names, "correct" means they were reported as not recognised.

## Directions, per field

| Field | Accuracy |
|---|---|
| times_per_day | 100.0% |
| slots | 100.0% |
| dose | 100.0% |
| dose_unit | 100.0% |
| timing | 100.0% |
| duration_days | 100.0% |
| as_needed | 100.0% |

## Failures (11)

| Case | Medicine | Problem | Detail |
|---|---|---|---|
| rx01 | Esita | identification: abstained | expected ['escitalopram'] |
| rx05 | Calpl | identification: abstained | expected ['acetaminophen'] |
| rx07 | Esita | identification: abstained | expected ['escitalopram'] |
| rx14 | Dispriin | identification: abstained | expected ['aspirin'] |
| rx19 | Esita | identification: abstained | expected ['escitalopram'] |
| rx33 | Ponstaan | identification: abstained | expected ['mefenamic acid'] |
| rx34 | Arinac | identification: abstained | expected ['ibuprofen', 'pseudoephedrine'] |
| rx35 | Arinac | identification: abstained | expected ['ibuprofen', 'pseudoephedrine'] |
| rx43 | Disprn | identification: abstained | expected ['aspirin'] |
| rx43 | Amxil | identification: abstained | expected ['amoxicillin'] |
| rx46 | Cocor | identification: abstained | expected ['bisoprolol'] |
