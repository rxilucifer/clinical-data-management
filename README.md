# Clinical Data Management Toolkit

A set of Python tools that act like a clinical data management team on a
fake clinical trial: generate trial data, check it, raise queries, and
prepare it in a standard format.

**All data is randomly generated. No real patients are involved.**

## Status
- [x] Phase 1: Fake trial dataset with planted mistakes
- [ ] Phase 2: Edit checks
- [ ] Phase 3: Query log
- [ ] Phase 4: SDTM-style mapping
- [ ] Phase 5: Data quality dashboard
- [ ] Phase 6: Data Validation Plan

## How to run
1. `pip install -r requirements.txt`
2. `python make_trial_data.py`