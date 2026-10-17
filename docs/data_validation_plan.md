# Data Validation Plan

**Study:** ABC101 (fictional)
**Version:** 1.0
**Date:** October 2026
**Author:** [Dr. Raj Akil Nomani]

> This is a teaching document for a fake clinical trial. All data is randomly generated and no real patients are involved.

## 1. Purpose

This plan describes how data from study ABC101 is checked for quality before it is prepared for analysis. It lists each edit check, why it exists, and what happens when a check finds a problem.

## 2. Scope

| Dataset | File | Content |
|---------|------|---------|
| Demographics | `data/demographics.csv` | Subject, site, sex, age, consent date, treatment arm |
| Vital signs | `data/vitals.csv` | Blood pressure, heart rate and weight at each visit |
| Adverse events | `data/adverse_events.csv` | Event term, dates, severity, seriousness |

The study has 120 subjects at 3 sites (S01, S02, S03). Each subject has 3 visits: Screening, Week 4 and Week 8.

## 3. Protocol rules used by the checks

These rules are fictional and were made up for this project.

- Participants must be aged 18 to 80 years.
- Sex is recorded as F or M.
- Informed consent must be signed before any study visit.
- Systolic and diastolic blood pressure, heart rate and weight are measured at every visit.
- Every adverse event must belong to an enrolled subject and have a term and valid dates.

## 4. Edit checks

| Check | Dataset | Rule | Type | Why it matters |
|-------|---------|------|------|----------------|
| DM-01 | Demographics | Age is not blank | Missing data | Age is needed to confirm the subject meets the inclusion range |
| DM-02 | Demographics | Age is between 18 and 80 | Range | A value outside the range is a typing error or an ineligible subject |
| DM-03 | Demographics | Sex is F or M | Valid values | Other codes break downstream analysis and SDTM mapping |
| DM-04 | Demographics | Each subject appears once | Duplicate | Repeated subjects distort counts and results |
| VS-01 | Vital signs | Systolic is not lower than diastolic | Cross-field logic | The two values were probably swapped or mistyped |
| VS-02 | Vital signs | Heart rate is between 40 and 200 | Range | Values outside this range are almost certainly entry errors |
| VS-03 | Vital signs | Weight is not blank | Missing data | Weight is a required measurement at every visit |
| VS-04 | Vital signs | Visit date is not before consent date | Date logic | No study procedure may happen before consent |
| AE-01 | Adverse events | End date is not before start date | Date logic | An event cannot end before it starts |
| AE-02 | Adverse events | Event term is not blank | Missing data | An event without a term cannot be assessed or coded |
| AE-03 | Adverse events | Subject exists in Demographics | Link between datasets | An event for an unknown subject points to a wrong ID or a missing enrolment |

## 5. Query management

1. `run_checks.py` runs all checks and saves the findings to `output/findings.csv`.
2. `make_query_log.py` turns each finding into a numbered query (Q-0001, Q-0002 and so on). It finds the subject's site, writes a message from a template, and sets the status to Open.
3. The site looks at the source document, corrects or confirms the value, and replies in the `site_response` column.
4. The data manager re-runs the checks. A query is closed when its check no longer flags the record.
5. Queries linked to a subject who is not in the study (site shown as Unknown) are investigated by the data manager before anything is sent to a site.

This project only creates queries with the status Open. Recording responses and closing queries is a manual step.

## 6. Data cleaning gate before SDTM

Only subjects with no open queries are mapped to the SDTM-style datasets. Subjects with open queries are held back until their queries are resolved. The list is saved in `output/sdtm/held_back_subjects.csv`.

Results of the current run:

- Subjects in the study: 120
- Held back because of open queries: 32
- Mapped as clean subjects: 88
- Records produced: DM 88, VS 1,056, AE 69

## 7. Testing the checks

`make_trial_data.py` plants 36 known mistakes in the data and saves them in `data/answer_key.csv`. `run_checks.py` compares its findings with that answer key.

- Planted mistakes: 36
- Caught: 36
- Missed: 0
- Extra findings: 0

This shows that every check works on the mistakes it was written for. It does not prove the checks would find unexpected problems in real data, and in real data the checks would be reviewed with a medical monitor and a statistician.

## 8. Assumptions and limitations

- All data is synthetic. Real trial data is messier and arrives from an electronic data capture (EDC) system.
- The protocol rules and ranges are fictional.
- There is no audit trail, user access control or formal system validation.
- There is no medical review and no MedDRA or drug coding of adverse events.
- The SDTM mapping is simplified. It leaves out many standard variables, controlled terminology, Define-XML and SAS transport (XPT) files.
- Query closing and site responses are not automated.

## 9. Possible next steps

- Track query responses and closure automatically.
- Add checks for visit windows, laboratory data and concomitant medications.
- Add MedDRA-style coding of adverse event terms using a practice dictionary.
- Add an audit trail that records every data change.

## 10. Change history

| Version | Date | Change |
|---------|------|--------|
| 1.0 | October 2026 | First version |