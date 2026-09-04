import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import pymysql

load_dotenv()

USUARIO = os.getenv("DB_USUARIO")
SENHA = os.getenv("DB_SENHA")
HOST = os.getenv("DB_HOST")
PORTA = int(os.getenv("DB_PORTA"))
DIALETO = os.getenv("DB_DIALETO")
BANCO_DESTINO = os.getenv("DB_DESTINO")


def criar_banco():
    """Cria o banco de dados no servidor MySQL, caso ainda nao exista."""
    conexao = pymysql.connect(
        host=HOST,
        port=PORTA,
        user=USUARIO,
        password=SENHA
    )
    try:
        with conexao.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS {BANCO_DESTINO} "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
        conexao.commit()
        print(f"Banco '{BANCO_DESTINO}' verificado/criado com sucesso.")
    finally:
        conexao.close()


def criar_tabelas():
    """Cria as tabelas customers, customer_monthly e payments no banco selecionado."""
    conexao = pymysql.connect(
        host=HOST,
        port=PORTA,
        user=USUARIO,
        password=SENHA,
        database=BANCO_DESTINO
    )
    try:
        with conexao.cursor() as cursor:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

            cursor.execute("DROP TABLE IF EXISTS payments;")
            cursor.execute("DROP TABLE IF EXISTS customer_monthly;")
            cursor.execute("DROP TABLE IF EXISTS customers;")

            cursor.execute("""
                CREATE TABLE customers (
                    customer_id VARCHAR(36) PRIMARY KEY,
                    full_name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    phone VARCHAR(50),
                    city VARCHAR(100),
                    state VARCHAR(10),
                    gender VARCHAR(10),
                    birth_date DATE,
                    acquisition_date DATE NOT NULL,
                    cohort_month DATE NOT NULL,
                    plan VARCHAR(50) NOT NULL,
                    contract_type VARCHAR(50) NOT NULL,
                    monthly_fee DECIMAL(10,2) NOT NULL,
                    current_status VARCHAR(20) NOT NULL,
                    churn_date DATE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            cursor.execute("""
                CREATE TABLE customer_monthly (
                    monthly_id INT AUTO_INCREMENT PRIMARY KEY,
                    customer_id VARCHAR(36) NOT NULL,
                    month_start DATE NOT NULL,
                    tenure_month INT NOT NULL,
                    active_flag TINYINT NOT NULL,
                    churn_flag TINYINT NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    monthly_fee DECIMAL(10,2) NOT NULL,
                    recognized_revenue DECIMAL(10,2) NOT NULL,
                    revenue_at_risk DECIMAL(10,2) NOT NULL,
                    days_overdue INT NOT NULL,
                    UNIQUE KEY uk_customer_month (customer_id, month_start),
                    CONSTRAINT fk_monthly_customer
                        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            cursor.execute("""
                CREATE TABLE payments (
                    payment_id INT AUTO_INCREMENT PRIMARY KEY,
                    customer_id VARCHAR(36) NOT NULL,
                    reference_month DATE NOT NULL,
                    due_date DATE NOT NULL,
                    payment_date DATE,
                    days_overdue INT NOT NULL,
                    payment_status VARCHAR(20) NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    UNIQUE KEY uk_customer_reference (customer_id, reference_month),
                    CONSTRAINT fk_payments_customer
                        FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            cursor.execute("CREATE INDEX idx_monthly_month ON customer_monthly(month_start);")
            cursor.execute("CREATE INDEX idx_monthly_customer ON customer_monthly(customer_id);")
            cursor.execute("CREATE INDEX idx_customers_cohort ON customers(cohort_month);")

            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

        conexao.commit()
        print("Tabelas criadas com sucesso.")
    finally:
        conexao.close()


def migrar_dados():
    """Le os dados do SQLite e insere nas tabelas ja existentes no MySQL."""
    sqlite_conn = sqlite3.connect("data/telecom_crm.sqlite")
    engine_mysql = create_engine(f"{DIALETO}://{USUARIO}:{SENHA}@{HOST}:{PORTA}/{BANCO_DESTINO}")

    # Limpa dados anteriores respeitando a ordem das dependencias
    with engine_mysql.connect() as conexao:
        conexao.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        conexao.execute(text("TRUNCATE TABLE payments;"))
        conexao.execute(text("TRUNCATE TABLE customer_monthly;"))
        conexao.execute(text("TRUNCATE TABLE customers;"))
        conexao.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        conexao.commit()

    tabelas = pd.read_sql(
        "SELECT name FROM sqlite_master WHERE type='table';",
        sqlite_conn
    )["name"].tolist()

    # Garante a ordem correta de insercao devido as chaves estrangeiras
    ordem_insercao = ["customers", "customer_monthly", "payments"]
    tabelas_ordenadas = [t for t in ordem_insercao if t in tabelas]

    for tabela in tabelas_ordenadas:
        print(f"Migrando tabela: {tabela}")
        df = pd.read_sql(f"SELECT * FROM {tabela}", sqlite_conn)
        df.to_sql(tabela, con=engine_mysql, if_exists="append", index=False)

    sqlite_conn.close()
    print("Migracao concluida.")


if __name__ == "__main__":
    criar_banco()
    criar_tabelas()
    migrar_dados()