# HR Workforce Attrition Dashboard: Power BI Specification

## Data model
Import one table, `data/processed_hr_analytics.csv`, and name it **`employees`** (1 row per employee, 1,000 rows).
(The SQL star schema in `sql/schema_and_queries.sql` holds the same data as dimensions and a fact table; the
Power BI report uses the flat CSV so it needs no database.)

## Calculated columns (employees table)
```dax
Overtime Bracket =
SWITCH(TRUE(),
    employees[overtime_hours] <= 10, "0-10",
    employees[overtime_hours] <= 20, "11-20",
    employees[overtime_hours] <= 30, "21-30",
    "31-40")
```
```dax
Compa Band =
SWITCH(TRUE(),
    employees[compa_ratio] < 0.85, "Below 0.85",
    employees[compa_ratio] < 1.0,  "0.85-1.00",
    employees[compa_ratio] < 1.15, "1.00-1.15",
    "Above 1.15")
```

## DAX measures
```dax
Total Headcount = COUNTROWS(employees)
```
```dax
Attrition Rate % =
DIVIDE(CALCULATE(COUNTROWS(employees), employees[attrition_status] = "Yes"), COUNTROWS(employees))
```
```dax
Avg Monthly Income = AVERAGE(employees[monthly_income])
```
```dax
Avg Tenure (Years) = AVERAGE(employees[tenure_years])
```
```dax
High Risk Active Employees =
CALCULATE(COUNTROWS(employees), employees[attrition_status] = "No", employees[flight_risk_level] = "High")
```

## Page layout
- **Top row:** KPI cards for Total Headcount, Attrition Rate %, Avg Monthly Income, High Risk Active Employees, plus a Department slicer.
- **Middle row:** column chart of Attrition Rate % by `department`; column chart of Attrition Rate % by `Overtime Bracket`.
- **Lower row:** column chart of Attrition Rate % by `Compa Band`; scatter chart of `compa_ratio` (X) vs `monthly_income` (Y), coloured by `attrition_status`.
- **Bottom:** table of active high-risk employees (filter: `attrition_status` = No, `flight_risk_level` = High) with employee_id, department, job_role, compa_ratio, overtime_hours and years_since_last_promotion.

Dataset is synthetic. Flight risk level = number of risk factors: overtime over 20 h, compa-ratio below 0.85,
promotion stagnation (rating 4+ and over 3 years), job satisfaction of 2 or less (High = 3+, Medium = 2).
