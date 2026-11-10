DROP TABLE IF EXISTS kpis_mensais;

CREATE TABLE
    kpis_mensais AS
SELECT
    month_start,
    COUNT(
        DISTINCT CASE
            WHEN status = 'ACTIVE' THEN customer_id
        END
    ) AS active_customers,
    COUNT(
        DISTINCT CASE
            WHEN status = 'GRACE_PERIOD' THEN customer_id
        END
    ) AS grace_period_customers,
    COUNT(
        DISTINCT CASE
            WHEN status = 'CHURN' THEN customer_id
        END
    ) AS churn_customers,
    -- KPI-06 (specs/kpis.spec.md): só GRACE_PERIOD é receita "sob risco" -
    -- receita de clientes em CHURN já foi perdida e não deve inflar este número.
    ROUND(
        SUM(
            CASE
                WHEN status = 'GRACE_PERIOD' THEN revenue_at_risk
                ELSE 0
            END
        ),
        2
    ) AS revenue_at_risk,
    ROUND(
        100.0 * COUNT(
            DISTINCT CASE
                WHEN churn_flag = 1 THEN customer_id
            END
        ) / NULLIF(COUNT(DISTINCT customer_id), 0),
        2
    ) AS churn_rate
FROM
    customer_monthly
GROUP BY
    month_start
ORDER BY
    month_start;