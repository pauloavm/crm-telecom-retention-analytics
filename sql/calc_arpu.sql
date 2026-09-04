DROP TABLE IF EXISTS arpu_mensal;

CREATE TABLE
    arpu_mensal AS
SELECT
    month_start,
    COUNT(
        DISTINCT CASE
            WHEN active_flag = 1 THEN customer_id
        END
    ) AS active_customers,
    ROUND(
        SUM(
            CASE
                WHEN active_flag = 1 THEN recognized_revenue
                ELSE 0
            END
        ),
        2
    ) AS total_revenue,
    ROUND(
        SUM(
            CASE
                WHEN active_flag = 1 THEN recognized_revenue
                ELSE 0
            END
        ) / NULLIF(
            COUNT(
                DISTINCT CASE
                    WHEN active_flag = 1 THEN customer_id
                END
            ),
            0
        ),
        2
    ) AS arpu
FROM
    customer_monthly
GROUP BY
    month_start
ORDER BY
    month_start;