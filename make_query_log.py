"""
Turns output/findings.csv into a query log, like the one a data manager
sends to trial sites. Saves it as Excel and CSV.
"""
from datetime import date
from pathlib import Path

import pandas as pd
from openpyxl.styles import Font, PatternFill

Path("output").mkdir(exist_ok=True)

findings = pd.read_csv("output/findings.csv")
dm = pd.read_csv("data/demographics.csv")

site_by_subject = (
    dm.drop_duplicates("subject_id").set_index("subject_id")["site_id"]
)

form_names = {
    "demographics": "Demographics",
    "vitals": "Vital Signs",
    "adverse_events": "Adverse Events",
}

# The message each site receives, one template per check
templates = {
    "DM-01": "Age is missing. Please enter the age from the source document.",
    "DM-02": "Age is entered as {value}, outside the protocol range of 18 to 80 years. Please check the source document.",
    "DM-03": "Sex is entered as '{value}'. Please enter F or M.",
    "DM-04": "This subject appears more than once on the Demographics form. Please confirm and remove the duplicate entry.",
    "VS-01": "Systolic blood pressure ({value}) is lower than the diastolic reading. Please check both values against the source document.",
    "VS-02": "Heart rate is entered as {value} bpm, outside the expected range of 40 to 200. Please verify.",
    "VS-03": "Weight is missing. Please enter the value from the source document.",
    "VS-04": "Visit date ({value}) is before the subject's consent date. Please verify both dates.",
    "AE-01": "Adverse event end date ({value}) is before the start date. Please verify both dates.",
    "AE-02": "Adverse event term is missing. Please enter the event as reported.",
    "AE-03": "This adverse event is linked to a subject ID that is not in the study database. Please confirm the subject ID.",
}


def clean(value):
    """Show 76.0 as 76 and empty values as (blank)."""
    if pd.isna(value):
        return "(blank)"
    try:
        number = float(value)
        return str(int(number)) if number.is_integer() else str(number)
    except (TypeError, ValueError):
            return str(value).replace(" 00:00:00", "")


log = findings.copy()
log["site_id"] = log["subject_id"].map(site_by_subject).fillna("Unknown")
log["form"] = log["dataset"].map(form_names)
log["query_text"] = [
    templates[check].format(value=clean(value))
    for check, value in zip(log["check_id"], log["value"])
]

log = log.sort_values(["site_id", "subject_id", "check_id"]).reset_index(drop=True)
log.insert(0, "query_id", [f"Q-{i:04d}" for i in range(1, len(log) + 1)])
log["date_raised"] = date.today().isoformat()
log["status"] = "Open"
log["site_response"] = ""
log["date_closed"] = ""

columns = ["query_id", "check_id", "site_id", "subject_id", "form", "field",
           "query_text", "date_raised", "status", "site_response", "date_closed"]
log = log[columns]

by_site = log.groupby("site_id").size().reset_index(name="queries")
by_check = log.groupby(["check_id", "form"]).size().reset_index(name="queries")

# ---------- Save ----------
log.to_csv("output/query_log.csv", index=False)

with pd.ExcelWriter("output/query_log.xlsx", engine="openpyxl") as writer:
    log.to_excel(writer, sheet_name="Query log", index=False)
    by_site.to_excel(writer, sheet_name="By site", index=False)
    by_check.to_excel(writer, sheet_name="By check", index=False)

    for sheet in writer.sheets.values():
        for cell in sheet[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="1F4E78")
        sheet.freeze_panes = "A2"
        for col in sheet.columns:
            longest = max(len(str(c.value)) if c.value is not None else 0 for c in col)
            sheet.column_dimensions[col[0].column_letter].width = min(longest + 2, 70)

    log_sheet = writer.sheets["Query log"]
    log_sheet.auto_filter.ref = log_sheet.dimensions

print(f"Created {len(log)} queries.")
print(by_site.to_string(index=False))