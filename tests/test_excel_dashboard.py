"""Dashboard em Excel (dashboards/dashboard_crm_telecom.xlsx) × métricas do app.

Lê os valores já calculados que vêm salvos no .xlsx (cenário padrão: sem filtros,
janela completa) e compara com analytics.py — Excel e Streamlit contam a mesma história.
"""
import math
from datetime import datetime
from pathlib import Path

import pytest

openpyxl = pytest.importorskip("openpyxl")

from analytics import Filters, cohort_retention, headline, monthly_kpis  # noqa: E402

XLSX = Path(__file__).resolve().parents[1] / "dashboards" / "dashboard_crm_telecom.xlsx"
COLS = dict(zip("CDEFGHIJKL", ["active_customers", "healthy_customers", "grace_customers", "churn_customers",
                               "base_customers", "total_revenue", "revenue_at_risk", "revenue_lost", "arpu",
                               "churn_rate"]))


@pytest.fixture(scope="module")
def values():
    return openpyxl.load_workbook(XLSX, data_only=True)


@pytest.fixture(scope="module")
def formulas():
    return openpyxl.load_workbook(XLSX)


def test_sheets_and_live_formulas(formulas):
    assert formulas.sheetnames[:2] == ["Dashboard", "Mensal"]
    dash = formulas["Dashboard"]
    for ref in ("B12", "F12", "J12", "N12", "D40"):
        assert str(dash[ref].value).startswith("="), f"{ref} deve ser fórmula, não valor fixo"
    assert {"f_plano", "f_contrato", "f_uf", "f_inicio", "f_fim"} <= set(formulas.defined_names)
    assert len(dash._charts) == 2
    assert len(dash.data_validations.dataValidation) == 5


def test_no_error_values(values):
    for ws in values.worksheets:
        for row in ws.iter_rows(values_only=True):
            for v in row:
                assert not (isinstance(v, str) and v.startswith("#") and v.endswith(("!", "?", "A"))), (ws.title, v)


def test_monthly_series_matches_app(values, shipped_db):
    app = monthly_kpis(shipped_db, Filters()).set_index("month_start")
    m = values["Mensal"]
    seen = 0
    for r in range(4, 28):
        month = m[f"B{r}"].value
        assert isinstance(month, datetime), "recalcule o arquivo após gerar (valores em cache ausentes)"
        row = app.loc[month.date().isoformat()]
        for col, key in COLS.items():
            expected = row[key] / 100 if key == "churn_rate" else row[key]
            assert math.isclose(m[f"{col}{r}"].value, expected, abs_tol=1e-6), (month, key)
        seen += 1
    assert seen == len(app) == 24


def test_kpi_cards_match_app_headline(values, shipped_db):
    h = headline(monthly_kpis(shipped_db, Filters()))
    d = values["Dashboard"]
    assert d["B12"].value == h["active"]
    assert math.isclose(d["F12"].value, h["arpu"], abs_tol=1e-6)
    assert math.isclose(d["J12"].value, h["churn_rate"] / 100, abs_tol=1e-9)
    assert math.isclose(d["N12"].value, h["revenue_at_risk"], abs_tol=1e-6)
    assert math.isclose(d["B13"].value, h["active_delta_pct"] / 100, abs_tol=1e-9)


def test_cohort_matrix_matches_app(values, shipped_db):
    co = cohort_retention(shipped_db, Filters())
    d = values["Dashboard"]
    for r in range(40, 64):
        cohort = d[f"B{r}"].value.date().isoformat()
        for t in range(13):
            got = d.cell(row=r, column=4 + t).value
            exp = co.loc[cohort, t] if t in co.columns else float("nan")
            if got in ("", None):
                assert math.isnan(exp), (cohort, t)
            else:
                assert math.isclose(got, exp / 100, abs_tol=1e-9), (cohort, t)
