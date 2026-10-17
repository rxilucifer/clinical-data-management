"""
Edit checks for the fake trial data.
Finds problems, saves them to output/findings.csv, and compares the result
with data/answer_key.csv to see if every planted mistake was caught.
"""
from pathlib import Path

import pandas as pd

Path("output").mkdir(exist_ok=True)

dm = pd.read_csv("data/demographics.csv", parse_dates=["consent_date"])
vs = pd.read_csv("data/vitals.csv", parse_dates=["visit_date"])
ae = pd.read_csv("data/adverse_events.csv", parse_dates=["start_date", "end_date"])

findings = []


def add(check_id, dataset, rows, field, issue):
    """Save one finding for every row that failed a check."""
    for _, row in rows.iterrows():
        findings.append({
            "check_id": check_id,
            "dataset": dataset,
            "subject_id": row["subject_id"],
            "field": field,
            "value": row[field],
            "issue": issue,
        })


# ---------- Demographics ----------
add("DM-01", "demographics", dm[dm["age"].isna()], "age", "Missing age")

# Trial rule: participants must be 18 to 80 years old
bad_age = dm[(dm["age"] < 18) | (dm["age"] > 80)]
add("DM-02", "demographics", bad_age, "age", "Age out of range")

add("DM-03", "demographics", dm[~dm["sex"].isin(["F", "M"])], "sex", "Invalid sex code")

# keep="first" flags only the extra copy of a repeated subject
add("DM-04", "demographics", dm[dm.duplicated("subject_id", keep="first")],
    "subject_id", "Duplicate subject")

# ---------- Vitals ----------
add("VS-01", "vitals", vs[vs["sbp"] < vs["dbp"]], "sbp", "Systolic lower than diastolic")

add("VS-02", "vitals", vs[(vs["heart_rate"] < 40) | (vs["heart_rate"] > 200)],
    "heart_rate", "Heart rate out of range")

add("VS-03", "vitals", vs[vs["weight_kg"].isna()], "weight_kg", "Missing weight")

consent = dm[["subject_id", "consent_date"]].drop_duplicates("subject_id")
vs_with_consent = vs.merge(consent, on="subject_id")
early = vs_with_consent[vs_with_consent["visit_date"] < vs_with_consent["consent_date"]]
add("VS-04", "vitals", early, "visit_date", "Visit before consent")

# ---------- Adverse events ----------
add("AE-01", "adverse_events", ae[ae["end_date"] < ae["start_date"]],
    "end_date", "AE end date before start date")

add("AE-02", "adverse_events", ae[ae["ae_term"].isna()], "ae_term", "Missing AE term")

add("AE-03", "adverse_events", ae[~ae["subject_id"].isin(dm["subject_id"])],
    "subject_id", "AE for unknown subject")

# ---------- Results ----------
f = pd.DataFrame(findings)
f.to_csv("output/findings.csv", index=False)

print("Findings by check:")
summary = f.groupby(["check_id", "issue"]).size().reset_index(name="count")
print(summary.to_string(index=False))
print(f"\nTotal findings: {len(f)}")

# ---------- Compare with the answer key ----------
key = pd.read_csv("data/answer_key.csv")
planted = set(zip(key["dataset"], key["subject_id"], key["problem"]))
found = set(zip(f["dataset"], f["subject_id"], f["issue"]))

print(f"\nPlanted mistakes: {len(planted)}")
print(f"Caught:           {len(planted & found)}")
print(f"Missed:           {len(planted - found)}")
print(f"Extra findings:   {len(found - planted)}")