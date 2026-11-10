"""Testes derivados de specs/kpis.spec.md (KPI-01..08) sobre uma base mínima conhecida."""
import pytest

from analytics import Filters, cohort_retention, headline, monthly_kpis


def by_month(df):
    return df.set_index("month_start")


def test_kpi01_kpi02_active_includes_grace_without_double_count(tiny_db):
    df = by_month(monthly_kpis(tiny_db, Filters()))
    feb = df.loc["2025-02-01"]
    # fev: A grace, C ativo, D ativo, B churn
    assert feb.active_customers == 3
    assert feb.healthy_customers == 2
    assert feb.grace_customers == 1
    assert (df.healthy_customers + df.grace_customers == df.active_customers).all()


def test_kpi03_kpi04_revenue_and_arpu(tiny_db):
    feb = by_month(monthly_kpis(tiny_db, Filters())).loc["2025-02-01"]
    assert feb.total_revenue == pytest.approx(200)  # 100 (A) + 50 (C) + 50 (D)
    assert feb.arpu == pytest.approx(200 / 3)


def test_kpi05_churn_rate_uses_starting_base(tiny_db):
    df = by_month(monthly_kpis(tiny_db, Filters()))
    assert df.loc["2025-02-01"].churn_rate == pytest.approx(25.0)  # 1 churn / 4 na base
    assert df.loc["2025-03-01"].churn_rate == pytest.approx(100 / 3)
    assert df.churn_rate.between(0, 100).all()


def test_kpi06_revenue_at_risk_counts_only_grace(tiny_db):
    df = by_month(monthly_kpis(tiny_db, Filters()))
    assert df.loc["2025-01-01"].revenue_at_risk == 50  # C em grace
    assert df.loc["2025-02-01"].revenue_at_risk == 100  # A em grace; B (churn) NÃO entra
    assert df.loc["2025-03-01"].revenue_at_risk == 0  # D churn NÃO entra


def test_kpi07_revenue_lost_counts_churn(tiny_db):
    df = by_month(monthly_kpis(tiny_db, Filters()))
    assert df.loc["2025-02-01"].revenue_lost == 100
    assert df.loc["2025-03-01"].revenue_lost == 50


def test_kpi06_risk_is_reported_for_every_month_not_only_global_last(tiny_db):
    """Regressão: o app original só somava risco quando month_start == MAX global."""
    df = monthly_kpis(tiny_db, Filters(month_start="2025-01-01", month_end="2025-02-01"))
    assert headline(df)["revenue_at_risk"] == 100


def test_kpi08_cohort_retention_uses_full_cohort_size(tiny_db):
    m = cohort_retention(tiny_db, Filters())
    jan = m.loc["2025-01-01"]
    assert jan[0] == pytest.approx(100.0)  # A, B, C ativos (C em grace conta como ativo)
    assert jan[1] == pytest.approx(200 / 3)  # B saiu
    assert m.loc["2025-02-01"][1] == pytest.approx(0.0)


def test_kpi08_window_does_not_rebase_older_cohorts(tiny_db):
    """Regressão: com janela iniciando em fev, a safra de jan não deve virar 100% no M1."""
    m = cohort_retention(tiny_db, Filters(month_start="2025-02-01", month_end="2025-03-01"))
    assert m.loc["2025-01-01"][1] == pytest.approx(200 / 3)


def test_kpi08_fully_churned_cohort_shows_zero_not_blank(tiny_db):
    """Safra que zerou mostra 0% nos meses seguintes (dentro da janela e dos dados)."""
    m = cohort_retention(tiny_db, Filters(plans=["P1"], states=["RJ"]))  # só o cliente B
    jan = m.loc["2025-01-01"]
    assert jan[0] == pytest.approx(100.0)
    assert jan[1] == pytest.approx(0.0)
    assert jan[2] == pytest.approx(0.0)  # B cancelou em fev: mar = 0%, não vazio
    assert 3 not in m.columns  # abril não existe nos dados


def test_kpi08_retention_bounded_and_non_increasing(shipped_db):
    m = cohort_retention(shipped_db, Filters())
    values = m.to_numpy()
    finite = values[~(values != values)]
    assert ((finite >= 0) & (finite <= 100)).all()
    for _, row in m.iterrows():
        row = row.dropna()
        assert (row.diff().dropna() <= 1e-9).all(), "retenção deve ser não-crescente"


def test_filters_by_plan_and_state(tiny_db):
    df = by_month(monthly_kpis(tiny_db, Filters(plans=["P2"], states=["SP"])))
    assert df.loc["2025-02-01"].active_customers == 2  # C e D
    assert df.loc["2025-03-01"].churn_customers == 1


def test_headline_uses_last_month_of_window(tiny_db):
    h = headline(monthly_kpis(tiny_db, Filters()))
    assert h["month"] == "2025-03-01"
    assert h["active"] == 2
    assert h["active_delta_pct"] == pytest.approx(-100 / 3)


def test_headline_empty():
    import pandas as pd

    assert headline(pd.DataFrame())["active"] == 0
