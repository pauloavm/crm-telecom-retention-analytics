DROP TABLE IF EXISTS cohort_retention;

CREATE TABLE
    cohort_retention AS
SELECT
    c.cohort_month,
    m.tenure_month,
    cs.cohort_customers,
    COUNT(
        DISTINCT CASE
            WHEN m.active_flag = 1 THEN m.customer_id
        END
    ) AS active_customers,
    ROUND(
        100.0 * COUNT(
            DISTINCT CASE
                WHEN m.active_flag = 1 THEN m.customer_id
            END
        ) / cs.cohort_customers,
        2
    ) AS retention_rate
FROM
    customers c
    JOIN customer_monthly m ON c.customer_id = m.customer_id
    JOIN (
        SELECT
            cohort_month,
            COUNT(*) AS cohort_customers
        FROM
            customers
        GROUP BY
            cohort_month
    ) cs ON c.cohort_month = cs.cohort_month
GROUP BY
    c.cohort_month,
    m.tenure_month,
    cs.cohort_customers
ORDER BY
    c.cohort_month,
    m.tenure_month;