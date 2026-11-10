"""E2E com Playwright: sobe o Streamlit de verdade e valida UI-01..06 da spec.

Execução:  pytest tests/e2e  (requer chromium do Playwright)
Variáveis:  CHROMIUM_PATH (binário opcional), APP_FILE (padrão app.py), E2E_SCREENSHOTS (pasta p/ salvar capturas).
"""
import csv
import io
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

pw = pytest.importorskip("playwright.sync_api")

ROOT = Path(__file__).resolve().parents[2]
APP_FILE = os.environ.get("APP_FILE", str(ROOT / "app.py"))
SHOTS = os.environ.get("E2E_SCREENSHOTS")
TITLE = "Telecom CRM & Retention Dashboard"


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def server():
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", APP_FILE, "--server.headless=true",
         f"--server.port={port}", "--browser.gatherUsageStats=false"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    url = f"http://127.0.0.1:{port}"
    for _ in range(60):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=1).close()
            break
        except OSError:
            time.sleep(0.5)
    yield url
    proc.terminate()
    proc.wait(timeout=10)


@pytest.fixture(scope="module")
def browser():
    with pw.sync_playwright() as p:
        # CHROMIUM_PATH permite usar um Chromium já instalado (ex.: /opt/pw-browsers/chromium)
        b = p.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or None)
        yield b
        b.close()


def open_app(browser, url, **ctx):
    page = browser.new_context(accept_downloads=True, **ctx).new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(url)
    page.get_by_text(TITLE).wait_for(timeout=60_000)
    page.locator(".js-plotly-plot").nth(2).wait_for(timeout=60_000)
    return page, errors


def no_streamlit_exception(page):
    return page.locator("[data-testid='stException']").count() == 0


def kpi_value(page, title):
    card = page.locator(".metric-card", has_text=title)
    return card.locator(".metric-value").inner_text()


def test_ui01_ui02_ui03_page_renders(browser, server):
    page, errors = open_app(browser, server, viewport={"width": 1440, "height": 1000})
    assert no_streamlit_exception(page)
    assert page.locator(".metric-card").count() == 4
    for title in ["Clientes Ativos", "ARPU", "Churn", "Receita sob Risco"]:
        assert page.locator(".metric-card", has_text=title).count() == 1, title
    assert page.locator(".js-plotly-plot").count() >= 3
    assert not errors, errors
    if SHOTS:
        page.screenshot(path=f"{SHOTS}/desktop.png", full_page=True)


def test_ui04_filter_updates_kpis(browser, server):
    page, _ = open_app(browser, server, viewport={"width": 1440, "height": 1000})
    value = page.locator(".metric-card", has_text="Clientes Ativos").locator(".metric-value")
    before = value.inner_text()
    plan_filter = page.locator("[data-testid='stMultiSelect']").first
    # Escolhe o plano pelo nome (o Streamlit recente inclui "Select all" na lista)
    plan_filter.click()
    page.get_by_role("option", name="Controle 10GB", exact=True).click()
    page.keyboard.press("Escape")
    pw.expect(plan_filter).to_contain_text("Controle 10GB", timeout=30_000)
    # expect() repete a verificação até o rerun do Streamlit terminar
    pw.expect(value).not_to_have_text(before, timeout=60_000)
    assert no_streamlit_exception(page)


def test_ui05_csv_export(browser, server):
    page, _ = open_app(browser, server, viewport={"width": 1440, "height": 1000})
    page.get_by_text("Visualizar e Exportar").click()
    with page.expect_download() as dl:
        page.get_by_role("button", name="Baixar").click()
    content = Path(dl.value.path()).read_text(encoding="utf-8")
    header = next(csv.reader(io.StringIO(content)))
    for col in ["month_start", "active_customers", "total_revenue", "arpu", "churn_rate", "revenue_at_risk"]:
        assert col in header
    assert len(content.splitlines()) == 25  # cabeçalho + 24 meses


def test_ui06_mobile_viewport(browser, server):
    page, errors = open_app(browser, server, viewport={"width": 390, "height": 844}, device_scale_factor=2)
    assert no_streamlit_exception(page)
    assert not errors
    if SHOTS:
        page.screenshot(path=f"{SHOTS}/mobile.png", full_page=True)
