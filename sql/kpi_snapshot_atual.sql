DROP TABLE IF EXISTS kpi_snapshot_atual;

CREATE TABLE
    kpi_snapshot_atual AS
SELECT
    month_start,
    COUNT(
        DISTINCT CASE
            WHEN status = 'ACTIVE' THEN customer_id
        END
    ) AS active_customers,
    ROUND(
        SUM(
            CASE
                WHEN status = 'ACTIVE' THEN recognized_revenue
                ELSE 0
            END
        ),
        2
    ) AS total_revenue,
    ROUND(
        SUM(
            CASE
                WHEN status = 'ACTIVE' THEN recognized_revenue
                ELSE 0
            END
        ) / NULLIF(
            COUNT(
                DISTINCT CASE
                    WHEN status = 'ACTIVE' THEN customer_id
                END
            ),
            0
        ),
        2
    ) AS arpu_atual,
    ROUND(
        100.0 * COUNT(
            DISTINCT CASE
                WHEN status = 'CHURN' THEN customer_id
            END
        ) / NULLIF(COUNT(DISTINCT customer_id), 0),
        2
    ) AS churn_rate_atual
FROM
    customer_monthly
WHERE
    month_start = (
        SELECT
            MAX(month_start)
        FROM
            customer_monthly
    )
GROUP BY
    month_start;