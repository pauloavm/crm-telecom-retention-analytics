DROP TABLE IF EXISTS kpi_snapshot_atual;

-- KPI-01/03/04 (specs/kpis.spec.md): clientes em GRACE_PERIOD continuam ativos
-- e com receita reconhecida, por isso entram em ativos, receita e ARPU.
CREATE TABLE
    kpi_snapshot_atual AS
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
