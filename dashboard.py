"""
Data quality dashboard for the fake clinical trial.
Run with: streamlit run dashboard.py
"""
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Clinical Data Quality Dashboard", layout="wide")


@st.cache_data
def load_data():
    log = pd.read_csv("output/query_log.csv")
    dm = pd.read_csv("data/demographics.csv").drop_duplicates("subject_id")
    held = pd.read_csv("output/sdtm/held_back_subjects.csv")
    return log, dm, held


log, dm, held = load_data()
held_in_study = held[held["subject_id"].isin(dm["subject_id"])]

st.title("Clinical Data Quality Dashboard")
st.caption("Study ABC101. All data is randomly generated. No real patients are involved.")

# ---------- Sidebar filters ----------
st.sidebar.header("Filters")
all_sites = sorted(log["site_id"].unique())
all_forms = sorted(log["form"].unique())
all_checks = sorted(log["check_id"].unique())

sites = st.sidebar.multiselect("Site", all_sites, default=all_sites)
forms = st.sidebar.multiselect("Form", all_forms, default=all_forms)
checks = st.sidebar.multiselect("Check", all_checks, default=all_checks)

filtered = log[
    log["site_id"].isin(sites)
    & log["form"].isin(forms)
    & log["check_id"].isin(checks)
]

# ---------- Headline numbers ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Subjects in study", len(dm))
c2.metric("Open queries (filtered)", int((filtered["status"] == "Open").sum()))
c3.metric("Subjects held back", len(held_in_study))
c4.metric("Clean subjects", len(dm) - len(held_in_study))

if filtered.empty:
    st.warning("No queries match these filters.")
    st.stop()

# ---------- Charts ----------
left, middle, right = st.columns(3)

with left:
    st.subheader("Queries by site")
    st.bar_chart(filtered.groupby("site_id").size().rename("queries"))

with middle:
    st.subheader("Queries per 100 subjects")
    subjects_per_site = dm.groupby("site_id").size()
    rate = (filtered.groupby("site_id").size() / subjects_per_site * 100).dropna()
    st.bar_chart(rate.round(1).rename("queries per 100 subjects"))
    st.caption("Unknown-site queries are left out because those subjects are not in the study.")

with right:
    st.subheader("Queries by check")
    st.bar_chart(filtered.groupby("check_id").size().rename("queries"))

# ---------- Table ----------
st.subheader("Query log")
st.dataframe(filtered, hide_index=True)

st.download_button(
    "Download filtered queries (CSV)",
    filtered.to_csv(index=False),
    file_name="filtered_queries.csv",
    mime="text/csv",
)

with st.expander("Subjects held back from SDTM (open queries)"):
    st.dataframe(held, hide_index=True)