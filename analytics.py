"""Camada de métricas do dashboard (pura, sem Streamlit) — testável isoladamente.

Todas as fórmulas seguem `specs/kpis.spec.md`. Os IDs (KPI-xx) citados nos
comentários apontam para a regra correspondente na especificação.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DB_CANDIDATES = [
    BASE_DIR / "data" / "telecom_crm_.sqlite",
    BASE_DIR / "data" / "telecom_crm.sqlite",
]


def find_database() -> Path | None:
    """Localiza o SQLite relativo ao repositório (não ao diretório corrente)."""
    return next((p for p in DB_CANDIDATES if p.exists()), None)


@dataclass(frozen=True)
class Filters:
    plans: Sequence[str] = field(default_factory=tuple)
    contracts: Sequence[str] = field(default_factory=tuple)
    states: Sequence[str] = field(default_factory=tuple)
    month_start: str | None = None
    month_end: str | None = None

    def customer_where(self) -> tuple[str, list]:
        """Filtros que dependem só do cliente (usados também no tamanho da safra)."""
        clauses, params = ["1=1"], []
        for col, values in (
            ("c.plan", self.plans),
            ("c.contract_type", self.contracts),
            ("c.state", self.states),
        ):
            if values:
                clauses.append(f"{col} IN ({','.join('?' * len(values))})")
                params.extend(values)
        return " AND ".join(clauses), params

    def full_where(self) -> tuple[str, list]:
        where, params = self.customer_where()
        if self.month_start and self.month_end:
            where += " AND cm.month_start BETWEEN ? AND ?"
            params += [self.month_start, self.month_end]
        return where, params


MONTHLY_COLUMNS = [
    "month_start",
    "active_customers",
    "healthy_customers",
    "grace_customers",
    "churn_customers",
    "base_customers",
    "total_revenue",
    "revenue_at_risk",
    "revenue_lost",
    "arpu",
    "churn_rate",
]


def monthly_kpis(conn: sqlite3.Connection, filters: Filters) -> pd.DataFrame:
    """Série mensal de KPIs (KPI-01..07)."""
    where, params = filters.full_where()
    sql = f"""
        SELECT
            cm.month_start,
            COUNT(DISTINCT CASE WHEN cm.active_flag = 1 THEN cm.customer_id END)      AS active_customers,   -- KPI-01
            COUNT(DISTINCT CASE WHEN cm.status = 'ACTIVE' THEN cm.customer_id END)    AS healthy_customers,  -- KPI-02
            COUNT(DISTINCT CASE WHEN cm.status = 'GRACE_PERIOD' THEN cm.customer_id END) AS grace_customers,
            COUNT(DISTINCT CASE WHEN cm.churn_flag = 1 THEN cm.customer_id END)       AS churn_customers,
            COUNT(DISTINCT cm.customer_id)                                            AS base_customers,
            COALESCE(SUM(cm.recognized_revenue), 0.0)                                 AS total_revenue,      -- KPI-03
            COALESCE(SUM(CASE WHEN cm.status = 'GRACE_PERIOD'
                              THEN cm.revenue_at_risk END), 0.0)                      AS revenue_at_risk,    -- KPI-06
            COALESCE(SUM(CASE WHEN cm.status = 'CHURN'
                              THEN cm.monthly_fee END), 0.0)                          AS revenue_lost        -- KPI-07
        FROM customer_monthly cm
        JOIN customers c ON c.customer_id = cm.customer_id
        WHERE {where}
        GROUP BY cm.month_start
        ORDER BY cm.month_start
    """
    df = pd.read_sql_query(sql, conn, params=params)
    active = df["active_customers"]
    base = df["base_customers"]
    df["arpu"] = np.where(active > 0, df["total_revenue"] / active.where(active > 0, 1), 0.0)  # KPI-04
    df["churn_rate"] = np.where(base > 0, df["churn_customers"] / base.where(base > 0, 1) * 100, 0.0)  # KPI-05
    return df[MONTHLY_COLUMNS]


def cohort_retention(conn: sqlite3.Connection, filters: Filters, max_tenure: int = 12) -> pd.DataFrame:
    """Matriz safra × tenure com retenção % (KPI-08).

    O denominador é o total de clientes adquiridos na safra (respeitando filtros
    de cliente, mas não a janela de datas), então a retenção nunca passa de 100%
    e cohorts anteriores à janela não são "re-baseados".
    """
    where, params = filters.full_where()
    cust_where, cust_params = filters.customer_where()
    sql = f"""
        WITH sizes AS (
            SELECT c.cohort_month, COUNT(*) AS cohort_size
            FROM customers c
            WHERE {cust_where}
            GROUP BY c.cohort_month
        )
        SELECT c.cohort_month, cm.tenure_month,
               COUNT(DISTINCT CASE WHEN cm.active_flag = 1 THEN cm.customer_id END) AS active,
               s.cohort_size
        FROM customer_monthly cm
        JOIN customers c ON c.customer_id = cm.customer_id
        JOIN sizes s ON s.cohort_month = c.cohort_month
        WHERE {where} AND cm.tenure_month <= ?
        GROUP BY c.cohort_month, cm.tenure_month, s.cohort_size
    """
    raw = pd.read_sql_query(sql, conn, params=cust_params + params + [max_tenure])
    if raw.empty:
        return pd.DataFrame()
    raw["retention"] = raw["active"] / raw["cohort_size"] * 100
    return raw.pivot(index="cohort_month", columns="tenure_month", values="retention").sort_index()


def headline(df_monthly: pd.DataFrame) -> dict:
    """KPIs dos cartões: último mês da janela filtrada e variação vs mês anterior."""
    if df_monthly.empty:
        return dict(active=0, active_delta_pct=0.0, arpu=0.0, churn_rate=0.0, revenue_at_risk=0.0, month=None)
    last = df_monthly.iloc[-1]
    prev = df_monthly.iloc[-2] if len(df_monthly) > 1 else last
    prev_active = int(prev["active_customers"])
    delta = (int(last["active_customers"]) - prev_active) / prev_active * 100 if prev_active else 0.0
    return dict(
        active=int(last["active_customers"]),
        active_delta_pct=float(delta),
        arpu=float(last["arpu"]),
        churn_rate=float(last["churn_rate"]),
        revenue_at_risk=float(last["revenue_at_risk"]),
        month=last["month_start"],
    )
