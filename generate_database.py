from faker import Faker
from datetime import date, timedelta
from pathlib import Path
from tqdm import tqdm  # Importação da biblioteca de barra de progresso
import sqlite3
import random
import re
import unicodedata
import uuid

# Configurações iniciais
fake = Faker("pt_BR")
Faker.seed(42)
random.seed(42)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "telecom_crm.sqlite"

TOTAL_CLIENTES = 1000000
DATA_INICIAL = date(2024, 1, 1)
DATA_FINAL = date(2025, 12, 31)


def primeiro_dia_mes(data):
    """Retorna o primeiro dia do mês da data informada."""
    return date(data.year, data.month, 1)


def proximo_mes(data):
    """Avança a data para o primeiro dia do mês seguinte."""
    if data.month == 12:
        return date(data.year + 1, 1, 1)
    return date(data.year, data.month + 1, 1)


def meses_entre(data_inicial, data_final):
    """Calcula a diferença em meses entre duas datas."""
    return (
        (data_final.year - data_inicial.year) * 12
        + data_final.month
        - data_inicial.month
    )


def normalizar_texto(texto):
    """Remove acentos, caracteres especiais e espaços, convertendo para minúsculas."""
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", "", texto.lower())


def criar_tabelas(conn):
    """Cria a estrutura de tabelas e índices no banco de dados SQLite."""
    conn.executescript("""
    PRAGMA foreign_keys = ON;

    DROP TABLE IF EXISTS payments;
    DROP TABLE IF EXISTS customer_monthly;
    DROP TABLE IF EXISTS customers;

    CREATE TABLE customers (
        customer_id TEXT PRIMARY KEY,
        full_name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        phone TEXT,
        city TEXT,
        state TEXT,
        gender TEXT,
        birth_date TEXT,
        acquisition_date TEXT NOT NULL,
        cohort_month TEXT NOT NULL,
        plan TEXT NOT NULL,
        contract_type TEXT NOT NULL,
        monthly_fee REAL NOT NULL,
        current_status TEXT NOT NULL,
        churn_date TEXT
    );

    CREATE TABLE customer_monthly (
        monthly_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id TEXT NOT NULL,
        month_start TEXT NOT NULL,
        tenure_month INTEGER NOT NULL,
        active_flag INTEGER NOT NULL,
        churn_flag INTEGER NOT NULL,
        status TEXT NOT NULL,
        monthly_fee REAL NOT NULL,
        recognized_revenue REAL NOT NULL,
        revenue_at_risk REAL NOT NULL,
        days_overdue INTEGER NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
        UNIQUE (customer_id, month_start)
    );

    CREATE TABLE payments (
        payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id TEXT NOT NULL,
        reference_month TEXT NOT NULL,
        due_date TEXT NOT NULL,
        payment_date TEXT,
        days_overdue INTEGER NOT NULL,
        payment_status TEXT NOT NULL,
        amount REAL NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
        UNIQUE (customer_id, reference_month)
    );

    CREATE INDEX idx_monthly_month
        ON customer_monthly(month_start);

    CREATE INDEX idx_monthly_customer
        ON customer_monthly(customer_id);

    CREATE INDEX idx_customers_cohort
        ON customers(cohort_month);
    """)


def gerar_clientes(conn):
    """Gera dados simulados para clientes e insere no banco de dados com barra de progresso."""
    used_emails = set()

    for _ in tqdm(range(TOTAL_CLIENTES), desc="Gerando clientes", unit="cliente"):
        customer_id = str(uuid.uuid4())

        nome = fake.name()
        base_email = f"{normalizar_texto(nome)}@{fake.free_email_domain()}"
        email = base_email

        contador = 1
        while email in used_emails:
            email = (
                f"{normalizar_texto(nome)}{contador}"
                f"@{fake.free_email_domain()}"
            )
            contador += 1

        used_emails.add(email)

        acquisition_date = fake.date_between(
            start_date=DATA_INICIAL,
            end_date=date(2025, 12, 20)
        )

        cohort_month = primeiro_dia_mes(acquisition_date)

        plan = random.choice([
            "Controle 10GB",
            "Controle 20GB",
            "Pós-pago 30GB",
            "Pós-pago 50GB",
            "Pós-pago 100GB"
        ])

        monthly_fee = {
            "Controle 10GB": 49.90,
            "Controle 20GB": 69.90,
            "Pós-pago 30GB": 89.90,
            "Pós-pago 50GB": 119.90,
            "Pós-pago 100GB": 169.90
        }[plan]

        contract_type = random.choice([
            "Monthly",
            "One year",
            "Two year"
        ])

        conn.execute("""
            INSERT INTO customers (
                customer_id,
                full_name,
                email,
                phone,
                city,
                state,
                gender,
                birth_date,
                acquisition_date,
                cohort_month,
                plan,
                contract_type,
                monthly_fee,
                current_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            customer_id,
            nome,
            email,
            fake.phone_number(),
            fake.city(),
            fake.estado_sigla(),
            random.choice(["F", "M", "Outro"]),
            fake.date_of_birth(
                minimum_age=18,
                maximum_age=75
            ).isoformat(),
            acquisition_date.isoformat(),
            cohort_month.isoformat(),
            plan,
            contract_type,
            monthly_fee,
            "ACTIVE"
        ))

        gerar_historico_cliente(
            conn,
            customer_id,
            acquisition_date,
            cohort_month,
            monthly_fee
        )


def gerar_historico_cliente(
    conn,
    customer_id,
    acquisition_date,
    cohort_month,
    monthly_fee
):
    """Gera o histórico mensal de faturamento e pagamentos de cada cliente."""
    mes = cohort_month
    churn_date = None

    while mes <= DATA_FINAL:
        tenure = meses_entre(cohort_month, mes)

        sorteio_atraso = random.random()

        if sorteio_atraso < 0.15:
            days_overdue = random.randint(1, 15)
        elif sorteio_atraso < 0.19:
            days_overdue = random.randint(16, 60)
        else:
            days_overdue = 0

        churn_probability = 0.025

        if tenure == 2:
            churn_probability = 0.18
        elif tenure in [1, 3, 4]:
            churn_probability = 0.07

        churn_by_behavior = random.random() < churn_probability
        churn_by_inadimplencia = days_overdue > 15

        is_churn = churn_by_behavior or churn_by_inadimplencia
        is_grace = 1 <= days_overdue <= 15

        if is_churn:
            status = "CHURN"
            active_flag = 0
            churn_flag = 1
            recognized_revenue = 0
            revenue_at_risk = monthly_fee
            churn_date = mes.isoformat()
        elif is_grace:
            status = "GRACE_PERIOD"
            active_flag = 1
            churn_flag = 0
            recognized_revenue = monthly_fee
            revenue_at_risk = monthly_fee
        else:
            status = "ACTIVE"
            active_flag = 1
            churn_flag = 0
            recognized_revenue = monthly_fee
            revenue_at_risk = 0

        conn.execute("""
            INSERT INTO customer_monthly (
                customer_id,
                month_start,
                tenure_month,
                active_flag,
                churn_flag,
                status,
                monthly_fee,
                recognized_revenue,
                revenue_at_risk,
                days_overdue
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            customer_id,
            mes.isoformat(),
            tenure,
            active_flag,
            churn_flag,
            status,
            monthly_fee,
            recognized_revenue,
            revenue_at_risk,
            days_overdue
        ))

        if days_overdue == 0:
            payment_status = "PAID"
            payment_date = mes + timedelta(days=random.randint(1, 8))
        elif days_overdue <= 15:
            payment_status = "GRACE_PERIOD"
            payment_date = mes + timedelta(days=days_overdue)
        else:
            payment_status = "OVERDUE"
            payment_date = None

        due_date = mes + timedelta(days=10)

        conn.execute("""
            INSERT INTO payments (
                customer_id,
                reference_month,
                due_date,
                payment_date,
                days_overdue,
                payment_status,
                amount
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            customer_id,
            mes.isoformat(),
            due_date.isoformat(),
            payment_date.isoformat() if payment_date else None,
            days_overdue,
            payment_status,
            monthly_fee
        ))

        if is_churn:
            break

        mes = proximo_mes(mes)

    if churn_date:
        conn.execute("""
            UPDATE customers
            SET current_status = 'CHURN',
                churn_date = ?
            WHERE customer_id = ?
        """, (churn_date, customer_id))


def main():
    """Função principal que orquestra a criação do banco de dados e a geração dos dados."""
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)

    try:
        print("Iniciando a criação do banco de dados e tabelas...")
        criar_tabelas(conn)

        gerar_clientes(conn)

        conn.commit()

        total = conn.execute(
            "SELECT COUNT(*) FROM customers"
        ).fetchone()[0]

        print(f"Banco criado com sucesso: {DB_PATH}")
        print(f"Total de clientes gerados e validados: {total}")

    finally:
        conn.close()


if __name__ == "__main__":
    main()