from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="HR Workforce Attrition Dashboard", page_icon="👥", layout="wide")
DATA = Path(__file__).parent / "data"
COLORS = {"Yes": "#D64545", "No": "#4E79A7"}  # attrition_status


@st.cache_data
def load():
    return (pd.read_csv(DATA / "processed_hr_analytics.csv"),
            pd.read_csv(DATA / "statistical_insights.csv"))


def rate(s):
    return (s == "Yes").mean() * 100


df, tests = load()

# ---------- Sidebar filters ----------
st.sidebar.header("Filters")
depts = sorted(df.department.unique())
chosen = st.sidebar.multiselect("Department", depts, default=depts)
ot = st.sidebar.radio("Overtime over 20h/month", ["All", "Yes", "No"], horizontal=True)
d = df[df.department.isin(chosen)]
if ot != "All":
    d = d[d.overtime_status == ot]

st.title("👥 HR Workforce Attrition & Productivity Dashboard")
st.caption("Synthetic dataset (1,000 employees). Risk level = number of risk factors: overtime over 20h, "
           "compa-ratio below 0.85, promotion stagnation, job satisfaction of 2 or less.")
if d.empty:
    st.warning("No employees match these filters.")
    st.stop()

active = d[d.attrition_status == "No"]
k1, k2, k3, k4 = st.columns(4)
k1.metric("Headcount", f"{len(d):,}")
k2.metric("Attrition rate", f"{rate(d.attrition_status):.1f}%")
k3.metric("Avg monthly income", f"${d.monthly_income.mean():,.0f}")
k4.metric("Active employees at high risk", f"{(active.flight_risk_level == 'High').sum():,}")

tab1, tab2, tab3, tab4 = st.tabs(["Attrition drivers", "Compensation", "Flight risk", "Statistical tests"])

with tab1:
    c1, c2 = st.columns(2)
    by_dept = d.groupby("department").attrition_status.apply(rate).reset_index(name="Attrition %")
    c1.plotly_chart(px.bar(by_dept, x="department", y="Attrition %", text_auto=".1f",
                           title="Attrition rate by department"), width="stretch")
    ot_b = pd.cut(d.overtime_hours, [-1, 10, 20, 30, 40], labels=["0-10", "11-20", "21-30", "31-40"])
    by_ot = d.groupby(ot_b, observed=True).attrition_status.apply(rate).reset_index(name="Attrition %")
    c2.plotly_chart(px.bar(by_ot, x="overtime_hours", y="Attrition %", text_auto=".1f",
                           title="Attrition rate by monthly overtime hours"), width="stretch")
    by_rf = d.groupby("risk_factors").attrition_status.apply(rate).reset_index(name="Attrition %")
    st.plotly_chart(px.bar(by_rf, x="risk_factors", y="Attrition %", text_auto=".1f",
                           title="Attrition rate by number of risk factors"), width="stretch")

with tab2:
    c1, c2 = st.columns(2)
    c1.plotly_chart(px.scatter(d, x="compa_ratio", y="monthly_income", color="attrition_status",
                               color_discrete_map=COLORS, hover_data=["employee_id", "job_role"],
                               title="Compa-ratio vs monthly income"), width="stretch")
    band = pd.cut(d.compa_ratio, [0, 0.85, 1.0, 1.15, 2], labels=["Below 0.85", "0.85-1.00", "1.00-1.15", "Above 1.15"])
    by_band = d.groupby(band, observed=True).attrition_status.apply(rate).reset_index(name="Attrition %")
    c2.plotly_chart(px.bar(by_band, x="compa_ratio", y="Attrition %", text_auto=".1f",
                           title="Attrition rate by compa-ratio band"), width="stretch")

with tab3:
    level = st.selectbox("Risk level of active employees", ["High", "Medium", "Low"])
    view = active[active.flight_risk_level == level].sort_values(["risk_factors", "burnout_risk_score"], ascending=False)
    st.write(f"{len(view):,} active employees with {level.lower()} flight risk")
    cols = ["employee_id", "department", "job_role", "tenure_years", "monthly_income", "compa_ratio",
            "overtime_hours", "years_since_last_promotion", "performance_rating", "job_satisfaction", "risk_factors"]
    st.dataframe(view[cols], width="stretch")
    st.download_button("Download this list (CSV)", view[cols].to_csv(index=False), f"{level.lower()}_risk_employees.csv")

with tab4:
    st.dataframe(tests, width="stretch")
    st.caption("A P-Value below 0.05 means the difference is unlikely to be chance. Tests use the full dataset.")
