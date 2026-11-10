"""Executa os modelos de sql/ (escritos p/ MySQL) no SQLite e valida as tabelas geradas."""
from pathlib import Path

import pandas as pd
import pytest

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"
MODELS = ["calc_arpu.sql", "cohort_analysis.sql", "kpis_mensais.sql", "kpi_snapshot_atual.sql"]


def run_models(conn):
    for name in MODELS:
        script = (SQL_DIR / name).read_text(encoding="utf-8")
        for stmt in filter(None, (s.strip() for s in script.split(";"))):
            conn.execute(stmt)
    conn.commit()


@pytest.fixture()
def models(db_copy):
    run_models(db_copy)
    return db_copy


def read(conn, table):
    return pd.read_sql_query(f"SELECT * FROM {table}", conn)


def test_models_are_idempotent(db_copy):
    run_models(db_copy)
    run_models(db_copy)
    assert len(read(db_copy, "kpi_snapshot_atual")) == 1


def test_cohort_retention_model_bounds(models):
    df = read(models, "cohort_retention")
    assert df.retention_rate.between(0, 100).all()
    assert (df.active_customers <= df.cohort_customers).all()


def test_snapshot_matches_last_month_of_kpis(models):
    snap = read(models, "kpi_snapshot_atual").iloc[0]
    kpis = read(models, "kpis_mensais").sort_values("month_start").iloc[-1]
    assert snap.month_start == kpis.month_start
    assert snap.active_customers == kpis.active_customers


def test_kpi06_model_revenue_at_risk_is_grace_only(models):
    df = read(models, "kpis_mensais").set_index("month_start")
    expected = pd.read_sql_query(
        "SELECT month_start, SUM(revenue_at_risk) r FROM customer_monthly WHERE status='GRACE_PERIOD' GROUP BY 1",
        models,
    ).set_index("month_start").r
    pd.testing.assert_series_equal(df.revenue_at_risk.loc[expected.index], expected.round(2), check_names=False)


def test_arpu_model_consistent(models):
    df = read(models, "arpu_mensal")
    recomputed = (df.total_revenue / df.active_customers).round(2)
    assert (recomputed - df.arpu).abs().max() < 0.011
