from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

ROLES = {  # department: [(job role, band midpoint = monthly income)]
    "Sales":       [("Sales Executive", 6500), ("Sales Representative", 4500)],
    "R&D":         [("Research Scientist", 7000), ("Laboratory Technician", 4800)],
    "HR":          [("HR Specialist", 5200), ("HR Manager", 9000)],
    "Marketing":   [("Marketing Analyst", 5500), ("Marketing Manager", 9500)],
    "Engineering": [("Software Engineer", 8500), ("Senior Engineer", 11500)],
}
DEPT_SHARE = [0.28, 0.25, 0.08, 0.15, 0.24]  # same order as ROLES

COLUMNS = ["employee_id", "department", "job_role", "band_midpoint", "tenure_years", "monthly_income",
           "overtime_hours", "distance_from_home", "job_satisfaction", "years_since_last_promotion",
           "performance_rating", "overtime_status", "compa_ratio", "promotion_stagnation",
           "attrition_status", "burnout_risk_score", "risk_factors", "flight_risk_level"]

def generate(n=1000, seed=42):
    rng = np.random.default_rng(seed)
    dept = rng.choice(list(ROLES), n, p=DEPT_SHARE)
    picks = [ROLES[d][rng.integers(2)] for d in dept]
    tenure = rng.integers(1, 20, n)
    df = pd.DataFrame({
        "employee_id": [f"EMP{i:04d}" for i in range(1, n + 1)],
        "department": dept,
        "job_role": [p[0] for p in picks],
        "band_midpoint": [p[1] for p in picks],
        "tenure_years": tenure,
        "overtime_hours": rng.integers(0, 40, n),
        "distance_from_home": rng.integers(1, 30, n),
        "job_satisfaction": rng.integers(1, 5, n),
        "years_since_last_promotion": [int(rng.integers(0, min(t, 8) + 1)) for t in tenure],
        "performance_rating": rng.choice([1, 2, 3, 4, 5], n, p=[0.05, 0.15, 0.40, 0.28, 0.12]),
    })
    df["monthly_income"] = (df["band_midpoint"] * rng.uniform(0.7, 1.3, n)).round().astype(int)
    df["overtime_status"] = np.where(df["overtime_hours"] > 20, "Yes", "No")  # chronic overtime = over 20 h/month
    df["compa_ratio"] = (df["monthly_income"] / df["band_midpoint"]).round(3)
    df["promotion_stagnation"] = (df["performance_rating"] >= 4) & (df["years_since_last_promotion"] > 3)

    # Attrition probability = base rate + extra risk for each driver
    p = (0.06 + 0.10 * (df["overtime_hours"] > 20) + 0.10 * (df["compa_ratio"] < 0.85)
         + 0.10 * df["promotion_stagnation"] + 0.05 * (df["job_satisfaction"] <= 2))
    df["attrition_status"] = np.where(rng.random(n) < p, "Yes", "No")

    # Feature engineering
    df["burnout_risk_score"] = ((df["overtime_hours"] / df["overtime_hours"].max()
                                 + df["distance_from_home"] / df["distance_from_home"].max()) / 2).round(3)
    df["risk_factors"] = ((df["overtime_hours"] > 20).astype(int) + (df["compa_ratio"] < 0.85).astype(int)
                          + df["promotion_stagnation"].astype(int) + (df["job_satisfaction"] <= 2).astype(int))
    df["flight_risk_level"] = pd.cut(df["risk_factors"], [-1, 1, 2, 4], labels=["Low", "Medium", "High"]).astype(str)
    return df[COLUMNS]


def chi_test(name, flag, df):
    chi2, p, _, _ = stats.chi2_contingency(pd.crosstab(flag, df["attrition_status"]))
    r = df.groupby(flag)["attrition_status"].apply(lambda s: (s == "Yes").mean() * 100)
    return {"Test": name, "Statistic": chi2, "P-Value": p, "Significant": p < 0.05,
            "Detail": f"Attrition {r[True]:.1f}% vs {r[False]:.1f}%"}

def run_hr_pipeline():
    df = generate()
    left, stayed = df[df.attrition_status == "Yes"], df[df.attrition_status == "No"]
    t, p_t = stats.ttest_ind(left["monthly_income"], stayed["monthly_income"], equal_var=False)  # Welch
    results = pd.DataFrame([
        chi_test("Chi-Square: overtime over 20h vs attrition", df["overtime_status"] == "Yes", df),
        chi_test("Chi-Square: compa-ratio below 0.85 vs attrition", df["compa_ratio"] < 0.85, df),
        chi_test("Chi-Square: promotion stagnation vs attrition", df["promotion_stagnation"], df),
        {"Test": "Welch T-Test: monthly income, left vs stayed", "Statistic": t, "P-Value": p_t,
         "Significant": p_t < 0.05,
         "Detail": f"Avg income {left.monthly_income.mean():,.0f} (left) vs {stayed.monthly_income.mean():,.0f} (stayed)"},
    ])
    print(results.to_string(index=False))

    DATA_DIR.mkdir(exist_ok=True)
    df.to_csv(DATA_DIR / "processed_hr_analytics.csv", index=False)
    results.to_csv(DATA_DIR / "statistical_insights.csv", index=False)
    print(f"\nExported {len(df)} employees and {len(results)} test results to {DATA_DIR}")


if __name__ == "__main__":
    run_hr_pipeline()
