"""Qualidade de dados do banco versionado (RN-01..07 da spec)."""
import pytest


def scalar(conn, sql):
    return conn.execute(sql).fetchone()[0]


def test_pk_and_unique_keys(shipped_db):
    assert scalar(shipped_db, "SELECT COUNT(*) - COUNT(DISTINCT customer_id) FROM customers") == 0
    assert scalar(shipped_db, "SELECT COUNT(*) - COUNT(DISTINCT email) FROM customers") == 0
    assert scalar(
        shipped_db,
        "SELECT COUNT(*) FROM (SELECT customer_id, month_start FROM customer_monthly GROUP BY 1,2 HAVING COUNT(*)>1)",
    ) == 0


@pytest.mark.parametrize("table", ["customer_monthly", "payments"])
def test_foreign_keys(shipped_db, table):
    orphans = scalar(
        shipped_db,
        f"SELECT COUNT(*) FROM {table} t LEFT JOIN customers c USING(customer_id) WHERE c.customer_id IS NULL",
    )
    assert orphans == 0


def test_rn01_rn02_rn03_status_matches_days_overdue(shipped_db):
    bad = scalar(
        shipped_db,
        """
        SELECT COUNT(*) FROM customer_monthly WHERE NOT (
            (status = 'GRACE_PERIOD' AND days_overdue BETWEEN 1 AND 15 AND active_flag=1 AND revenue_at_risk=monthly_fee)
         OR (status = 'CHURN' AND churn_flag=1 AND active_flag=0 AND recognized_revenue=0)
         OR (status = 'ACTIVE' AND days_overdue = 0 AND active_flag=1 AND revenue_at_risk=0)
        )
        """,
    )
    assert bad == 0
    # todo atraso > 15 dias resulta em churn
    assert scalar(shipped_db, "SELECT COUNT(*) FROM customer_monthly WHERE days_overdue > 15 AND status <> 'CHURN'") == 0


def test_rn04_churn_is_terminal(shipped_db):
    after = scalar(
        shipped_db,
        """
        SELECT COUNT(*) FROM customer_monthly m
        JOIN (SELECT customer_id, month_start AS churn_month FROM customer_monthly WHERE status='CHURN') x
          USING(customer_id)
        WHERE m.month_start > x.churn_month
        """,
    )
    assert after == 0
    assert scalar(shipped_db, "SELECT MAX(n) FROM (SELECT COUNT(*) n FROM customer_monthly WHERE status='CHURN' GROUP BY customer_id)") <= 1


def test_rn05_current_status_consistent(shipped_db):
    bad = scalar(
        shipped_db,
        """
        SELECT COUNT(*) FROM customers c
        LEFT JOIN customer_monthly m ON m.customer_id = c.customer_id AND m.status = 'CHURN'
        WHERE (c.current_status = 'CHURN') <> (m.customer_id IS NOT NULL)
           OR (m.customer_id IS NOT NULL AND c.churn_date <> m.month_start)
        """,
    )
    assert bad == 0


def test_rn06_history_is_contiguous_from_cohort(shipped_db):
    bad = scalar(
        shipped_db,
        """
        SELECT COUNT(*) FROM customer_monthly m JOIN customers c USING(customer_id)
        WHERE m.month_start <> date(c.cohort_month, '+' || m.tenure_month || ' months')
        """,
    )
    assert bad == 0
    starts_at_zero = scalar(
        shipped_db,
        "SELECT COUNT(*) FROM (SELECT customer_id FROM customer_monthly GROUP BY 1 HAVING MIN(tenure_month) <> 0)",
    )
    assert starts_at_zero == 0


def test_rn07_payments_mirror_monthly(shipped_db):
    mismatch = scalar(
        shipped_db,
        """
        SELECT COUNT(*) FROM customer_monthly m
        LEFT JOIN payments p ON p.customer_id = m.customer_id AND p.reference_month = m.month_start
        WHERE p.customer_id IS NULL OR p.days_overdue <> m.days_overdue
        """,
    )
    assert mismatch == 0
    assert scalar(shipped_db, "SELECT COUNT(*) FROM payments") == scalar(shipped_db, "SELECT COUNT(*) FROM customer_monthly")


def test_dates_are_iso_and_month_starts(shipped_db):
    assert scalar(shipped_db, "SELECT COUNT(*) FROM customer_monthly WHERE strftime('%d', month_start) <> '01'") == 0
    assert scalar(shipped_db, "SELECT COUNT(*) FROM customers WHERE date(acquisition_date) IS NULL") == 0
