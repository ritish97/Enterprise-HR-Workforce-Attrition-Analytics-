-- ----------------------------------------------------------------------------
-- 1. STAGING TABLE (columns match the CSV exactly, in order)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS Fact_Employee_History CASCADE;
DROP TABLE IF EXISTS Dim_Performance_Reviews CASCADE;
DROP TABLE IF EXISTS Dim_Job_Roles CASCADE;
DROP TABLE IF EXISTS Dim_Departments CASCADE;
DROP TABLE IF EXISTS Staging_Employees CASCADE;

CREATE TABLE Staging_Employees (
    employee_id                VARCHAR(20),
    department                 VARCHAR(100),
    job_role                   VARCHAR(100),
    band_midpoint              NUMERIC(12, 2),
    tenure_years               INT,
    monthly_income             NUMERIC(12, 2),
    overtime_hours             INT,
    distance_from_home         INT,
    job_satisfaction           INT,
    years_since_last_promotion INT,
    performance_rating         INT,
    overtime_status            VARCHAR(3),
    compa_ratio                NUMERIC(6, 3),
    promotion_stagnation       BOOLEAN,
    attrition_status           VARCHAR(3),
    burnout_risk_score         NUMERIC(6, 3),
    risk_factors               INT,
    flight_risk_level          VARCHAR(10)
);

-- ----------------------------------------------------------------------------
-- 2. DIMENSIONS AND FACT TABLE
-- ----------------------------------------------------------------------------
CREATE TABLE Dim_Departments (
    department_id   SERIAL PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE
);
INSERT INTO Dim_Departments (department_name)
SELECT DISTINCT department FROM Staging_Employees ORDER BY department;

CREATE TABLE Dim_Job_Roles (
    job_role_id          SERIAL PRIMARY KEY,
    job_role_title       VARCHAR(100) NOT NULL UNIQUE,
    base_salary_midpoint NUMERIC(12, 2) NOT NULL
);
INSERT INTO Dim_Job_Roles (job_role_title, base_salary_midpoint)
SELECT DISTINCT job_role, band_midpoint FROM Staging_Employees ORDER BY job_role;

CREATE TABLE Dim_Performance_Reviews (
    review_id          SERIAL PRIMARY KEY,
    performance_rating INT NOT NULL UNIQUE CHECK (performance_rating BETWEEN 1 AND 5),
    rating_description VARCHAR(50) NOT NULL
);
INSERT INTO Dim_Performance_Reviews (performance_rating, rating_description) VALUES
    (1, 'Needs Improvement'), (2, 'Below Expectations'), (3, 'Meets Expectations'),
    (4, 'Exceeds Expectations'), (5, 'Outstanding');

CREATE TABLE Fact_Employee_History (
    employee_id                VARCHAR(20) PRIMARY KEY,
    department_id              INT REFERENCES Dim_Departments(department_id),
    job_role_id                INT REFERENCES Dim_Job_Roles(job_role_id),
    review_id                  INT REFERENCES Dim_Performance_Reviews(review_id),
    tenure_years               INT NOT NULL,
    monthly_income             NUMERIC(12, 2) NOT NULL,
    overtime_hours             INT NOT NULL,
    overtime_status            VARCHAR(3) CHECK (overtime_status IN ('Yes', 'No')),
    distance_from_home         INT NOT NULL,
    job_satisfaction           INT CHECK (job_satisfaction BETWEEN 1 AND 4),
    years_since_last_promotion INT NOT NULL,
    compa_ratio                NUMERIC(6, 3),
    burnout_risk_score         NUMERIC(6, 3),
    flight_risk_level          VARCHAR(10),
    attrition_status           VARCHAR(3) CHECK (attrition_status IN ('Yes', 'No'))
);
INSERT INTO Fact_Employee_History
SELECT s.employee_id, d.department_id, jr.job_role_id, pr.review_id, s.tenure_years, s.monthly_income,
       s.overtime_hours, s.overtime_status, s.distance_from_home, s.job_satisfaction,
       s.years_since_last_promotion, s.compa_ratio, s.burnout_risk_score, s.flight_risk_level,
       s.attrition_status
FROM Staging_Employees s
JOIN Dim_Departments d          ON d.department_name = s.department
JOIN Dim_Job_Roles jr           ON jr.job_role_title = s.job_role
JOIN Dim_Performance_Reviews pr ON pr.performance_rating = s.performance_rating;

-- ============================================================================
-- 3. ANALYTICAL QUERIES
-- ============================================================================

-- Query 1: Attrition by department vs the company average (window functions)
WITH dept AS (
    SELECT d.department_name,
           COUNT(*) AS headcount,
           SUM(CASE WHEN f.attrition_status = 'Yes' THEN 1 ELSE 0 END) AS leavers
    FROM Fact_Employee_History f
    JOIN Dim_Departments d ON f.department_id = d.department_id
    GROUP BY d.department_name
)
SELECT department_name,
       headcount,
       leavers,
       ROUND(100.0 * leavers / headcount, 2)                    AS attrition_rate_pct,
       ROUND(100.0 * SUM(leavers) OVER () / SUM(headcount) OVER (), 2) AS company_rate_pct,
       RANK() OVER (ORDER BY 1.0 * leavers / headcount DESC)    AS risk_rank
FROM dept
ORDER BY risk_rank;


-- Query 2: Overtime hours vs resignation rate
SELECT CASE WHEN overtime_hours <= 10 THEN '0-10 hours'
            WHEN overtime_hours <= 20 THEN '11-20 hours'
            WHEN overtime_hours <= 30 THEN '21-30 hours'
            ELSE '31+ hours (High Burnout)' END AS overtime_bracket,
       COUNT(*) AS total_employees,
       SUM(CASE WHEN attrition_status = 'Yes' THEN 1 ELSE 0 END) AS resigned_employees,
       ROUND(100.0 * SUM(CASE WHEN attrition_status = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS resignation_rate_pct,
       ROUND(AVG(monthly_income), 2) AS avg_monthly_income
FROM Fact_Employee_History
GROUP BY 1
ORDER BY MIN(overtime_hours);


-- Query 3: Promotion lag - active high performers stuck for over 3 years
SELECT f.employee_id,
       d.department_name,
       jr.job_role_title,
       pr.performance_rating,
       f.years_since_last_promotion,
       f.monthly_income,
       f.compa_ratio,
       f.overtime_hours,
       f.flight_risk_level
FROM Fact_Employee_History f
JOIN Dim_Departments d          ON f.department_id = d.department_id
JOIN Dim_Job_Roles jr           ON f.job_role_id = jr.job_role_id
JOIN Dim_Performance_Reviews pr ON f.review_id = pr.review_id
WHERE f.attrition_status = 'No'
  AND pr.performance_rating >= 4
  AND f.years_since_last_promotion > 3
ORDER BY CASE f.flight_risk_level WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END,
         f.years_since_last_promotion DESC, f.monthly_income ASC;
