"""
Builds a simplified SDTM-style version of the trial data (DM, VS, AE).

Rule used here: only "clean" subjects (no open queries) are mapped.
Subjects with open queries are held back until their queries are resolved.

Writes:
  output/sdtm/dm.csv, vs.csv, ae.csv
  output/sdtm/held_back_subjects.csv
"""
from pathlib import Path

import pandas as pd

STUDYID = "ABC101"

Path("output/sdtm").mkdir(parents=True, exist_ok=True)

dm_raw = pd.read_csv("data/demographics.csv")
vs_raw = pd.read_csv("data/vitals.csv")
ae_raw = pd.read_csv("data/adverse_events.csv")
findings = pd.read_csv("output/findings.csv")

# ---------- Which subjects are clean? ----------
all_subjects = set(dm_raw["subject_id"])
flagged = set(findings["subject_id"])
clean_subjects = all_subjects - flagged

reasons = (
    findings.groupby("subject_id")["check_id"]
    .apply(lambda s: ", ".join(sorted(set(s))))
    .reset_index(name="open_query_checks")
)
reasons.to_csv("output/sdtm/held_back_subjects.csv", index=False)

dm_raw = dm_raw[dm_raw["subject_id"].isin(clean_subjects)].reset_index(drop=True)
vs_raw = vs_raw[vs_raw["subject_id"].isin(clean_subjects)].reset_index(drop=True)
ae_raw = ae_raw[ae_raw["subject_id"].isin(clean_subjects)].reset_index(drop=True)

site_by_subject = dm_raw.set_index("subject_id")["site_id"]


def usubjid(subject_id):
    """Unique subject ID: study + site + subject number."""
    return f"{STUDYID}-{site_by_subject[subject_id]}-{subject_id.split('-')[1]}"


# ---------- DM: Demographics ----------
dm = pd.DataFrame({
    "STUDYID": STUDYID,
    "DOMAIN": "DM",
    "USUBJID": [usubjid(s) for s in dm_raw["subject_id"]],
    "SUBJID": dm_raw["subject_id"].str.split("-").str[1],
    "SITEID": dm_raw["site_id"],
    "AGE": dm_raw["age"].astype(int),
    "AGEU": "YEARS",
    "SEX": dm_raw["sex"],
    "ARMCD": dm_raw["arm"].map({"Drug": "DRUG", "Placebo": "PBO"}),
    "ARM": dm_raw["arm"],
    "RFICDTC": dm_raw["consent_date"],
})

# ---------- VS: Vital signs (one row per test per visit) ----------
tests = {
    "sbp": ("SYSBP", "Systolic Blood Pressure", "mmHg"),
    "dbp": ("DIABP", "Diastolic Blood Pressure", "mmHg"),
    "heart_rate": ("HR", "Heart Rate", "beats/min"),
    "weight_kg": ("WEIGHT", "Weight", "kg"),
}
visit_numbers = {"Screening": 1, "Week 4": 2, "Week 8": 3}

rows = []
for _, r in vs_raw.iterrows():
    for column, (testcd, test, unit) in tests.items():
        value = r[column]
        if pd.isna(value):
            continue  # no result, no record
        rows.append({
            "STUDYID": STUDYID,
            "DOMAIN": "VS",
            "USUBJID": usubjid(r["subject_id"]),
            "VSTESTCD": testcd,
            "VSTEST": test,
            "VSORRES": f"{value:g}",
            "VSORRESU": unit,
            "VSSTRESC": f"{value:g}",
            "VSSTRESN": float(value),
            "VSSTRESU": unit,
            "VISITNUM": visit_numbers[r["visit"]],
            "VISIT": r["visit"],
            "VSDTC": r["visit_date"],
        })
vs = pd.DataFrame(rows)
vs.insert(3, "VSSEQ", vs.groupby("USUBJID").cumcount() + 1)

# ---------- AE: Adverse events ----------
ae = pd.DataFrame({
    "STUDYID": STUDYID,
    "DOMAIN": "AE",
    "USUBJID": [usubjid(s) for s in ae_raw["subject_id"]],
    "AETERM": ae_raw["ae_term"],
    "AESEV": ae_raw["severity"].str.upper(),
    "AESER": ae_raw["serious"],
    "AESTDTC": ae_raw["start_date"],
    "AEENDTC": ae_raw["end_date"],
})
ae.insert(3, "AESEQ", ae.groupby("USUBJID").cumcount() + 1)

# ---------- Simple conformance checks ----------
assert dm["USUBJID"].is_unique, "DM has repeated subjects"
assert set(vs["USUBJID"]) <= set(dm["USUBJID"]), "VS has subjects not in DM"
assert set(ae["USUBJID"]) <= set(dm["USUBJID"]), "AE has subjects not in DM"
assert dm["SEX"].isin(["F", "M"]).all(), "Unexpected SEX value"
assert ae["AESEV"].isin(["MILD", "MODERATE", "SEVERE"]).all(), "Unexpected AESEV value"
assert ae["AESER"].isin(["Y", "N"]).all(), "Unexpected AESER value"

# ---------- Save ----------
dm.to_csv("output/sdtm/dm.csv", index=False)
vs.to_csv("output/sdtm/vs.csv", index=False, float_format="%g")
ae.to_csv("output/sdtm/ae.csv", index=False)

held_in_study = len(all_subjects & flagged)
print(f"Subjects in study:         {len(all_subjects)}")
print(f"Held back (open queries):  {held_in_study}")
print(f"Mapped (clean subjects):   {len(clean_subjects)}")
print(f"DM rows: {len(dm)}   VS rows: {len(vs)}   AE rows: {len(ae)}")
print("Conformance checks passed.")