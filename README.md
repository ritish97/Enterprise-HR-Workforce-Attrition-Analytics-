Live : https://ezurm3oghbvcb5emt2ztgk.streamlit.app/
# Enterprise HR Workforce Attrition & Productivity Engine

An end-to-end HR analytics project: statistical driver tests, risk scoring, an Excel cost model, SQL star schema,
a Power BI dashboard and an interactive Streamlit app. **The data is synthetic** (1,000 employees, modelled on the
IBM HR Analytics schema), so the findings show what the method reveals, not real company results.

| Component | Technology | File | Purpose |
| :--- | :--- | :--- | :--- |
| Statistical pipeline | Python (`pandas`, `scipy`) | `python/hr_analytics_pipeline.py` | Data generation, hypothesis tests, risk features |
| Financial model | Python (`xlsxwriter`) | `excel/generate_excel_model.py` | Compensation bands and attrition cost, with live formulas |
| Data warehouse | PostgreSQL | `sql/schema_and_queries.sql` | Star schema and window-function queries |
| Executive BI | Power BI | `powerbi/` | Dashboard (`.pbix`) and specification |
| Interactive app | Streamlit | `app.py` | Filterable dashboard with flight-risk lists |

## Business problem
Replacing an employee commonly costs 1.5x their annual salary or more (recruiting, training, lost productivity) [1].
This project finds what drives voluntary attrition and which current employees are most at risk.

## Key findings (1,000 employees, 17.1% attrition)
1. **Overtime**: employees working over 20 overtime hours a month leave at **21.2%** vs 13.8% (about 1.5x; chi-square p = 0.003).
2. **Relative pay matters, absolute pay does not**: employees with a compa-ratio below 0.85 (paid under 85% of their job band midpoint) leave at **25.0%** vs 14.3% (p < 0.001) and make up 38% of all leavers. Average income of leavers vs stayers ($6,955 vs $7,154) is not significantly different (Welch t-test p = 0.36).
3. **Promotion stagnation**: high performers (rating 4+) without a promotion for over 3 years leave at **26.1%** vs 15.4% (p = 0.002).
4. **Risk factors add up**: attrition rises from 7.7% with no risk factors to 30.3% with three.
5. **Departments**: Marketing has the highest attrition (23.2%) and R&D the lowest (14.2%).
6. **Who to act on now**: 66 active employees are at high risk (3+ risk factors) and 271 at medium risk.
7. **Illustrative cost**: 171 leavers at 1.5x annual salary is about $22.5M in replacement cost (synthetic salaries).

## Recommendations
- **Cap chronic overtime** and rebalance workloads for staff above 20 overtime hours a month.
- **Audit pay bands annually** and prioritise employees below 0.85 compa-ratio.
- **Alert HR partners** when a high performer passes 3 years without a promotion.
- **Review the 66 high-risk active employees** with their managers (list available in the Streamlit app).
- **Investigate Marketing**, where attrition is well above the company average.

## Project structure
```
hr-workforce-analytics/
├── data/        processed_hr_analytics.csv, statistical_insights.csv
├── excel/       generate_excel_model.py, hr_compensation_benchmarks.xlsx
├── python/      hr_analytics_pipeline.py
├── sql/         schema_and_queries.sql
├── powerbi/     dashboard_spec.md (and the .pbix dashboard)
├── app.py       Streamlit dashboard
├── requirements.txt
└── README.md
```
## Data definitions
- `overtime_status` = Yes when `overtime_hours` is over 20 per month.
- `compa_ratio` = `monthly_income` / job-role band midpoint.
- `promotion_stagnation` = performance rating 4+ and more than 3 years since last promotion.
- `risk_factors` counts four flags: overtime over 20 h, compa-ratio below 0.85, promotion stagnation, job satisfaction of 2 or less. `flight_risk_level` is High (3+), Medium (2) or Low (0-1).
- `burnout_risk_score` = average of overtime hours and commute distance, each divided by its maximum.

## References
1. Boushey, H., & Glynn, S. J. (2012). There are significant business costs to replacing employees. *Center for American Progress*.
2. IBM HR Analytics Employee Attrition & Performance Dataset. Kaggle.
3. Agresti, A. (2018). *An Introduction to Categorical Data Analysis*. 3rd Edition. Wiley.

**Author**: Ritish Kumar Yadav
