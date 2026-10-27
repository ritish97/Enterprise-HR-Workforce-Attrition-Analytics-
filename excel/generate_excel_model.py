from pathlib import Path
import pandas as pd
import xlsxwriter
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "excel" / "hr_compensation_benchmarks.xlsx"

def generate_excel():
    df = pd.read_csv(ROOT / "data" / "processed_hr_analytics.csv")
    g = df.groupby("job_role").agg(
        headcount=("employee_id", "count"), avg_income=("monthly_income", "mean"),
        midpoint=("band_midpoint", "first"), avg_ot=("overtime_hours", "mean"),
        leavers=("attrition_status", lambda s: int((s == "Yes").sum()))).reset_index()
    g["avg_income"] = g["avg_income"].round(0)
    g["avg_ot"] = g["avg_ot"].round(1)

    OUT.parent.mkdir(exist_ok=True)
    wb = xlsxwriter.Workbook(OUT)
    head = wb.add_format({"bold": True, "bg_color": "#4F81BD", "font_color": "white", "border": 1, "text_wrap": True})
    money, pct, plain = (wb.add_format({"num_format": "$#,##0", "border": 1}),
                         wb.add_format({"num_format": "0.0%", "border": 1}), wb.add_format({"border": 1}))

    s1 = wb.add_worksheet("Compensation_Band_Model")
    for c, h in enumerate(["Job Role", "Headcount", "Avg Monthly Income", "Band Midpoint", "Compa-Ratio", "Avg Overtime Hours"]):
        s1.write(0, c, h, head)
    for r, row in enumerate(g.itertuples(), start=1):
        s1.write(r, 0, row.job_role, plain); s1.write(r, 1, row.headcount, plain)
        s1.write(r, 2, row.avg_income, money); s1.write(r, 3, row.midpoint, money)
        s1.write_formula(r, 4, f"=C{r+1}/D{r+1}", pct, row.avg_income / row.midpoint)
        s1.write(r, 5, row.avg_ot, plain)
    s1.set_column(0, 5, 20)

    s2 = wb.add_worksheet("Attrition_Cost_Calculator")
    for c, h in enumerate(["Job Role", "Leavers", "Avg Annual Salary", "Recruitment (0.3x)", "Training (0.2x)",
                           "Lost Productivity (1.0x)", "Cost per Leaver", "Total Attrition Cost"]):
        s2.write(0, c, h, head)
    for r, row in enumerate(g.itertuples(), start=1):
        sal = row.avg_income * 12
        s2.write(r, 0, row.job_role, plain); s2.write(r, 1, row.leavers, plain)
        s2.write_formula(r, 2, f"='Compensation_Band_Model'!C{r+1}*12", money, sal)
        s2.write_formula(r, 3, f"=C{r+1}*0.3", money, sal * 0.3)
        s2.write_formula(r, 4, f"=C{r+1}*0.2", money, sal * 0.2)
        s2.write_formula(r, 5, f"=C{r+1}*1.0", money, sal * 1.0)
        s2.write_formula(r, 6, f"=SUM(D{r+1}:F{r+1})", money, sal * 1.5)
        s2.write_formula(r, 7, f"=B{r+1}*G{r+1}", money, sal * 1.5 * row.leavers)
    n = len(g) + 1
    s2.write(n, 0, "TOTAL", head)
    s2.write_formula(n, 1, f"=SUM(B2:B{n})", plain, int(g.leavers.sum()))
    s2.write_formula(n, 7, f"=SUM(H2:H{n})", money, float((g.avg_income * 12 * 1.5 * g.leavers).sum()))
    s2.set_column(0, 7, 22)
    wb.close()
    print(f"Excel model generated at: {OUT}")


if __name__ == "__main__":
    generate_excel()
