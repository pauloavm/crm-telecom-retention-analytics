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


def test_snapshot_matches_last_month_of_series(models):
    """KPI-01/04: o snapshot dos cartões é o último mês das séries mensais (ativos incluem Grace)."""
    snap = read(models, "kpi_snapshot_atual").iloc[0]
    arpu = read(models, "arpu_mensal").sort_values("month_start").iloc[-1]
    kpis = read(models, "kpis_mensais").sort_values("month_start").iloc[-1]
    assert snap.month_start == arpu.month_start == kpis.month_start
    assert snap.active_customers == arpu.active_customers
    assert snap.arpu_atual == arpu.arpu
    assert snap.churn_rate_atual == kpis.churn_rate


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


def test_sql_models_match_dashboard_metrics(models):
    """O resultado materializado (Power BI) e o app (analytics.py) contam a mesma história."""
    import numpy as np

    from analytics import Filters, cohort_retention, monthly_kpis

    app = monthly_kpis(models, Filters()).set_index("month_start")
    kpis = read(models, "kpis_mensais").set_index("month_start")
    arpu = read(models, "arpu_mensal").set_index("month_start")
    assert (kpis.active_customers == app.healthy_customers).all()
    assert (kpis.grace_period_customers == app.grace_customers).all()
    assert np.allclose(kpis.churn_rate, app.churn_rate.round(2))
    assert np.allclose(kpis.revenue_at_risk, app.revenue_at_risk.round(2))
    assert (arpu.active_customers == app.active_customers).all()
    assert np.allclose(arpu.arpu, app.arpu.round(2))

    sql_cohort = read(models, "cohort_retention")
    app_cohort = cohort_retention(models, Filters(), max_tenure=99).stack().reset_index()
    app_cohort.columns = ["cohort_month", "tenure_month", "app"]
    joined = sql_cohort.merge(app_cohort, on=["cohort_month", "tenure_month"])
    assert len(joined) == len(sql_cohort)
    assert np.allclose(joined.retention_rate, joined.app.round(2))


def test_generate_table_view_sqlite_backend(tmp_path):
    """generate_table_view.py --sqlite reproduz no SQLite as tabelas que iam para o MySQL."""
    import shutil
    import sqlite3

    import generate_table_view as gtv
    from tests.conftest import SHIPPED_DB

    db = tmp_path / "copy.sqlite"
    shutil.copy(SHIPPED_DB, db)
    counts = gtv.atualizar_tabelas_resumo_sqlite(db)
    assert counts == {"arpu_mensal": 24, "cohort_retention": 300, "kpis_mensais": 24, "kpi_snapshot_atual": 1}
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 1000


def test_shipped_db_has_summary_tables(shipped_db):
    """O SQLite versionado já traz as tabelas resumo prontas (sem precisar de MySQL)."""
    tables = {r[0] for r in shipped_db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"arpu_mensal", "cohort_retention", "kpis_mensais", "kpi_snapshot_atual"} <= tables
