"""Testes do app Streamlit sem navegador (streamlit.testing.AppTest)."""
import os
from pathlib import Path

import pytest

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest
APP_FILE = os.environ.get("APP_FILE", str(Path(__file__).resolve().parents[1] / "app.py"))


@pytest.fixture()
def app():
    at = AppTest.from_file(APP_FILE, default_timeout=60)
    at.run()
    return at


def test_app_runs_without_exception(app):
    assert not app.exception


def test_app_has_filters(app):
    labels = [m.label for m in app.multiselect]
    assert labels == ["Plano do Cliente", "Tipo de Contrato", "Estado (UF)"]


def test_app_filter_rerun_without_exception(app):
    app.multiselect[0].select(app.multiselect[0].options[0]).run()
    assert not app.exception


def test_app_narrow_window_still_shows_revenue_at_risk(app):
    """KPI-06 + cartões: janela que termina antes do último mês global não zera o risco."""
    slider = app.select_slider[0]
    months = slider.options
    slider.set_range(months[0], months[-4]).run()
    assert not app.exception
    html = "".join(m.value for m in app.markdown)
    risk_block = html.split("Receita sob Risco", 1)[1][:400]
    assert "R$ 0.00" not in risk_block and "R$ 0,00" not in risk_block
