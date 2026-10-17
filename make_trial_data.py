"""
Creates a fake clinical trial dataset with deliberate mistakes.
All data is randomly generated. No real patients are involved.

Writes:
  data/demographics.csv
  data/vitals.csv
  data/adverse_events.csv
  data/answer_key.csv   (the mistakes we planted, so we can test our checks)
"""
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

random.seed(7)
Path("data").mkdir(exist_ok=True)

N_SUBJECTS = 120
sites = ["S01", "S02", "S03"]
visits = [("Screening", 0), ("Week 4", 28), ("Week 8", 56)]
ae_terms = ["Headache", "Nausea", "Dizziness", "Fatigue",
            "Rash", "Cough", "Diarrhoea", "Back pain"]
study_start = date(2025, 1, 1)

demographics, vitals, adverse = [], [], []
consent_by_subject = {}

# ---------- 1. Build clean data ----------
for i in range(1, N_SUBJECTS + 1):
    sid = f"ABC-{i:03d}"
    consent = study_start + timedelta(days=random.randint(0, 200))
    consent_by_subject[sid] = consent

    demographics.append({
        "subject_id": sid,
        "site_id": random.choice(sites),
        "sex": random.choice(["F", "M"]),
        "age": random.randint(18, 80),
        "consent_date": consent,
        "arm": random.choice(["Drug", "Placebo"]),
    })

    for visit, offset in visits:
        jitter = 0 if offset == 0 else random.randint(-2, 2)
        vitals.append({
            "subject_id": sid,
            "visit": visit,
            "visit_date": consent + timedelta(days=offset + jitter),
            "sbp": random.randint(100, 160),
            "dbp": random.randint(60, 100),
            "heart_rate": random.randint(55, 100),
            "weight_kg": round(random.uniform(48, 105), 1),
        })

    for _ in range(random.choice([0, 0, 1, 1, 2])):
        start = consent + timedelta(days=random.randint(1, 55))
        severity = random.choice(["Mild", "Mild", "Moderate", "Severe"])
        serious = "Y" if severity == "Severe" and random.random() < 0.5 else "N"
        adverse.append({
            "ae_id": len(adverse) + 1,
            "subject_id": sid,
            "ae_term": random.choice(ae_terms),
            "start_date": start,
            "end_date": start + timedelta(days=random.randint(1, 14)),
            "severity": severity,
            "serious": serious,
        })

dm = pd.DataFrame(demographics)
vs = pd.DataFrame(vitals)
ae = pd.DataFrame(adverse)

# ---------- 2. Plant mistakes (and keep an answer key) ----------
key = []


def log(dataset, subject_id, field, problem):
    key.append({"dataset": dataset, "subject_id": subject_id,
                "field": field, "problem": problem})


def pick(pool, n):
    """Pick n rows that have not been used for a mistake yet."""
    chosen = random.sample(pool, n)
    for c in chosen:
        pool.remove(c)
    return chosen


dm_pool = list(range(len(dm)))
vs_pool = list(range(len(vs)))
ae_pool = list(range(len(ae)))

# Demographics
for i in pick(dm_pool, 5):
    dm.loc[i, "age"] = None
    log("demographics", dm.loc[i, "subject_id"], "age", "Missing age")
for i in pick(dm_pool, 3):
    dm.loc[i, "age"] = 150
    log("demographics", dm.loc[i, "subject_id"], "age", "Age out of range")
for i in pick(dm_pool, 2):
    dm.loc[i, "sex"] = "X"
    log("demographics", dm.loc[i, "subject_id"], "sex", "Invalid sex code")

# Vitals
for i in pick(vs_pool, 4):
    vs.loc[i, "sbp"] = random.randint(72, 80)
    vs.loc[i, "dbp"] = random.randint(105, 115)
    log("vitals", vs.loc[i, "subject_id"], "sbp/dbp", "Systolic lower than diastolic")
for i in pick(vs_pool, 3):
    vs.loc[i, "heart_rate"] = 300
    log("vitals", vs.loc[i, "subject_id"], "heart_rate", "Heart rate out of range")
for i in pick(vs_pool, 5):
    vs.loc[i, "weight_kg"] = None
    log("vitals", vs.loc[i, "subject_id"], "weight_kg", "Missing weight")
for i in pick(vs_pool, 3):
    sid = vs.loc[i, "subject_id"]
    vs.loc[i, "visit_date"] = consent_by_subject[sid] - timedelta(days=5)
    log("vitals", sid, "visit_date", "Visit before consent")

# Adverse events
for i in pick(ae_pool, 4):
    ae.loc[i, "end_date"] = ae.loc[i, "start_date"] - timedelta(days=2)
    log("adverse_events", ae.loc[i, "subject_id"], "end_date", "AE end date before start date")
for i in pick(ae_pool, 3):
    ae.loc[i, "ae_term"] = None
    log("adverse_events", ae.loc[i, "subject_id"], "ae_term", "Missing AE term")

# Rows that point to patients who do not exist
for sid in ["ABC-998", "ABC-999"]:
    start = study_start + timedelta(days=60)
    ae = pd.concat([ae, pd.DataFrame([{
        "ae_id": int(ae["ae_id"].max()) + 1, "subject_id": sid,
        "ae_term": "Headache", "start_date": start,
        "end_date": start + timedelta(days=3),
        "severity": "Mild", "serious": "N",
    }])], ignore_index=True)
    log("adverse_events", sid, "subject_id", "AE for unknown subject")

# Duplicate patients
for i in pick(dm_pool, 2):
    dm = pd.concat([dm, dm.loc[[i]]], ignore_index=True)
    log("demographics", dm.loc[i, "subject_id"], "subject_id", "Duplicate subject")

# ---------- 3. Save ----------
dm.to_csv("data/demographics.csv", index=False)
vs.to_csv("data/vitals.csv", index=False)
ae.to_csv("data/adverse_events.csv", index=False)
pd.DataFrame(key).to_csv("data/answer_key.csv", index=False)

print(f"demographics: {len(dm)} rows")
print(f"vitals: {len(vs)} rows")
print(f"adverse events: {len(ae)} rows")
print(f"planted mistakes: {len(key)}")