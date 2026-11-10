"""Testes do gerador sintético (generate_database.py) em escala reduzida."""
import sqlite3
from datetime import date

import pytest

import generate_database as gen


@pytest.mark.parametrize(
    "a,b,expected",
    [(date(2024, 1, 1), date(2024, 1, 31), 0), (date(2024, 1, 1), date(2025, 3, 1), 14), (date(2024, 12, 1), date(2025, 1, 1), 1)],
)
def test_meses_entre(a, b, expected):
    assert gen.meses_entre(a, b) == expected


def test_proximo_mes_vira_ano():
    assert gen.proximo_mes(date(2024, 12, 15)) == date(2025, 1, 1)
    assert gen.primeiro_dia_mes(date(2024, 5, 31)) == date(2024, 5, 1)


def test_normalizar_texto():
    assert gen.normalizar_texto("João da Silva-Ávila") == "joaodasilvaavila"


@pytest.fixture()
def generated(tmp_path, monkeypatch):
    monkeypatch.setattr(gen, "TOTAL_CLIENTES", 300)
    monkeypatch.setattr(gen, "DB_PATH", tmp_path / "gen.sqlite")
    gen.random.seed(7)
    gen.Faker.seed(7)
    gen.main()
    conn = sqlite3.connect(tmp_path / "gen.sqlite")
    yield conn
    conn.close()


def test_generator_respects_business_rules(generated):
    q = lambda s: generated.execute(s).fetchone()[0]  # noqa: E731
    assert q("SELECT COUNT(*) FROM customers") == 300
    assert q("SELECT COUNT(*) FROM customer_monthly WHERE days_overdue > 15 AND status <> 'CHURN'") == 0
    assert q("SELECT COUNT(*) FROM customer_monthly WHERE status='GRACE_PERIOD' AND days_overdue NOT BETWEEN 1 AND 15") == 0
    assert q("SELECT COUNT(*) FROM customers WHERE current_status='CHURN' AND churn_date IS NULL") == 0
    assert q("SELECT COUNT(*) FROM customer_monthly WHERE month_start > '2025-12-01'") == 0


def test_generator_churn_peaks_at_tenure_2(generated):
    """A curva simulada concentra churn no 3º mês (tenure 2), base do insight de onboarding."""
    rows = generated.execute(
        "SELECT tenure_month, COUNT(*) FROM customer_monthly WHERE churn_flag=1 GROUP BY 1 ORDER BY 2 DESC"
    ).fetchall()
    assert rows[0][0] == 2
