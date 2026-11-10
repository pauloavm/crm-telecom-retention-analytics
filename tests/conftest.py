import shutil
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SHIPPED_DB = ROOT / "data" / "telecom_crm_.sqlite"


@pytest.fixture(scope="session")
def shipped_db():
    """Conexão somente-leitura com o banco versionado no repositório."""
    conn = sqlite3.connect(f"file:{SHIPPED_DB}?mode=ro", uri=True)
    yield conn
    conn.close()


@pytest.fixture()
def db_copy(tmp_path):
    """Cópia gravável do banco (para executar os scripts SQL de agregação)."""
    dst = tmp_path / "db.sqlite"
    shutil.copy(SHIPPED_DB, dst)
    conn = sqlite3.connect(dst)
    yield conn
    conn.close()


@pytest.fixture()
def tiny_db():
    """Base mínima construída à mão: resultados esperados calculáveis de cabeça.

    Safra 2025-01 (3 clientes) e safra 2025-02 (1 cliente), plano/UF variados.
        A: ACTIVE jan, GRACE fev, ACTIVE mar
        B: ACTIVE jan, CHURN fev (terminal)
        C: GRACE  jan, ACTIVE fev, ACTIVE mar
        D: (safra fev) ACTIVE fev, CHURN mar
    """
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE customers (customer_id TEXT PRIMARY KEY, plan TEXT, contract_type TEXT,
            state TEXT, cohort_month TEXT, monthly_fee REAL, current_status TEXT);
        CREATE TABLE customer_monthly (customer_id TEXT, month_start TEXT, tenure_month INT,
            active_flag INT, churn_flag INT, status TEXT, monthly_fee REAL,
            recognized_revenue REAL, revenue_at_risk REAL, days_overdue INT);
        INSERT INTO customers VALUES
            ('A','P1','Monthly','SP','2025-01-01',100,'ACTIVE'),
            ('B','P1','Monthly','RJ','2025-01-01',100,'CHURN'),
            ('C','P2','One year','SP','2025-01-01',50,'ACTIVE'),
            ('D','P2','Monthly','SP','2025-02-01',50,'CHURN');
        INSERT INTO customer_monthly VALUES
            ('A','2025-01-01',0,1,0,'ACTIVE',100,100,0,0),
            ('A','2025-02-01',1,1,0,'GRACE_PERIOD',100,100,100,5),
            ('A','2025-03-01',2,1,0,'ACTIVE',100,100,0,0),
            ('B','2025-01-01',0,1,0,'ACTIVE',100,100,0,0),
            ('B','2025-02-01',1,0,1,'CHURN',100,0,100,30),
            ('C','2025-01-01',0,1,0,'GRACE_PERIOD',50,50,50,3),
            ('C','2025-02-01',1,1,0,'ACTIVE',50,50,0,0),
            ('C','2025-03-01',2,1,0,'ACTIVE',50,50,0,0),
            ('D','2025-02-01',0,1,0,'ACTIVE',50,50,0,0),
            ('D','2025-03-01',1,0,1,'CHURN',50,0,50,20);
        """
    )
    yield conn
    conn.close()
