# MediLens evaluation

Synthetic set: 174 medicines on 50 printed prescriptions (`evaluation/cases.jsonl`, ground truth written by hand).

| Metric | Value |
|---|---|
| Medicine lines detected | 100.0% |
| Extra (non-medicine) lines taken as medicines | 0 |
| Known names identified correctly (incl. typos) | 100.0% |
| **Wrong matches (dangerous)** | **0** |
| Medicines fully correct (identity + every direction field) | 97.1% |

## Identification by group

| Group | Correct | Abstained ("not recognised") | Wrong |
|---|---|---|---|
| invented name | 11 | 0 | 0 |
| known name | 143 | 0 | 0 |
| typo | 15 | 0 | 0 |
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

## Failures (5)

| Case | Medicine | Problem | Detail |
|---|---|---|---|
| rx01 | Esita | identification: abstained | expected ['escitalopram'] |
| rx07 | Esita | identification: abstained | expected ['escitalopram'] |
| rx19 | Esita | identification: abstained | expected ['escitalopram'] |
| rx34 | Arinac | identification: abstained | expected ['ibuprofen', 'pseudoephedrine'] |
| rx35 | Arinac | identification: abstained | expected ['ibuprofen', 'pseudoephedrine'] |
