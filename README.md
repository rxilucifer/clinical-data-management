# Clinical Data Management Toolkit

A set of Python tools that act like a clinical data management team on a
fake clinical trial: generate trial data, check it, raise queries, and
prepare it in a standard format.

**All data is randomly generated. No real patients are involved.**

## Status
- [x] Phase 1: Fake trial dataset with planted mistakes
- [x] Phase 2: Edit checks
- [x] Phase 3: Query log
- [ ] Phase 4: SDTM-style mapping
- [ ] Phase 5: Data quality dashboard
- [ ] Phase 6: Data Validation Plan

## How to run
1. `pip install -r requirements.txt`
2. `python make_trial_data.py` creates the fake trial data in `data/`
3. `python run_checks.py` runs the edit checks and compares them with the planted mistakes
4. `python make_query_log.py` creates the query log in `output/`

## Edit checks

| Check | What it looks for |
|-------|-------------------|
| DM-01 | Missing age |
| DM-02 | Age outside the 18 to 80 inclusion range |
| DM-03 | Sex other than F or M |
| DM-04 | Duplicate subject |
| VS-01 | Systolic blood pressure lower than diastolic |
| VS-02 | Heart rate outside 40 to 200 |
| VS-03 | Missing weight |
| VS-04 | Visit date before consent date |
| AE-01 | Adverse event end date before start date |
| AE-02 | Missing adverse event term |
| AE-03 | Adverse event for a subject not in the study |

`run_checks.py` compares its findings with the 36 mistakes planted in
`data/answer_key.csv`. Result: 36 caught, 0 missed, 0 extra findings.

## Query log

`make_query_log.py` turns the edit check findings into a query log, like the
ones data managers send to trial sites. Each query has an ID, site, subject,
form, field, a message, and a status. A sample is in `output/query_log.csv`.