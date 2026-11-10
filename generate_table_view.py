"""Materializa as tabelas resumo (modelos de /sql) em MySQL ou em SQLite.

Uso:
    python generate_table_view.py                 # MySQL (variáveis DB_* no .env)
    python generate_table_view.py --sqlite        # SQLite em data/telecom_crm_.sqlite
    python generate_table_view.py --sqlite outro.sqlite

Os mesmos arquivos .sql rodam nos dois bancos, então o resultado do MySQL pode
ser reproduzido por qualquer pessoa só com o SQLite versionado no repositório.
"""
import argparse
import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PASTA_SQL = BASE_DIR / "sql"
SQLITE_PADRAO = BASE_DIR / "data" / "telecom_crm_.sqlite"

ARQUIVOS_SQL = [
    "calc_arpu.sql",
    "cohort_analysis.sql",
    "kpis_mensais.sql",
    "kpi_snapshot_atual.sql"
]

TABELAS_RESUMO = ["arpu_mensal", "cohort_retention", "kpis_mensais", "kpi_snapshot_atual"]


def obter_configuracao_obrigatoria(nome: str) -> str:
    valor = os.getenv(nome)
    if valor is None:
        raise RuntimeError(f"Variável de ambiente obrigatória não definida: {nome}")
    return valor


def comandos_sql(caminho_arquivo):
    """Lê um arquivo .sql e devolve cada instrução separadamente."""
    conteudo = Path(caminho_arquivo).read_text(encoding="utf-8")
    return [c.strip() for c in conteudo.split(";") if c.strip()]


def executar_arquivo_sql(cursor, caminho_arquivo):
    """Executa cada instrução de um arquivo .sql."""
    for comando in comandos_sql(caminho_arquivo):
        cursor.execute(comando)


def executar_modelos(conexao):
    """Recria todas as tabelas resumo usando uma conexão DB-API (MySQL ou SQLite)."""
    cursor = conexao.cursor()
    for nome_arquivo in ARQUIVOS_SQL:
        print(f"Executando: {nome_arquivo}")
        executar_arquivo_sql(cursor, PASTA_SQL / nome_arquivo)
    conexao.commit()


def atualizar_tabelas_resumo():
    """Conecta no MySQL e recria todas as tabelas resumo a partir dos arquivos .sql."""
    import pymysql
    from dotenv import load_dotenv

    load_dotenv()
    conexao = pymysql.connect(
        host=obter_configuracao_obrigatoria("DB_HOST"),
        port=int(os.getenv("DB_PORTA", "3306")),
        user=obter_configuracao_obrigatoria("DB_USUARIO"),
        password=obter_configuracao_obrigatoria("DB_SENHA"),
        database=obter_configuracao_obrigatoria("DB_DESTINO"),
    )
    try:
        executar_modelos(conexao)
        print("Todas as tabelas resumo foram atualizadas com sucesso (MySQL).")
    finally:
        conexao.close()


def atualizar_tabelas_resumo_sqlite(caminho=SQLITE_PADRAO):
    """Recria as tabelas resumo dentro do SQLite e devolve a contagem de linhas de cada uma."""
    caminho = Path(caminho)
    if not caminho.exists():
        raise FileNotFoundError(f"Banco SQLite não encontrado: {caminho}. Rode generate_database.py antes.")
    conexao = sqlite3.connect(caminho)
    try:
        executar_modelos(conexao)
        contagens = {
            t: conexao.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in TABELAS_RESUMO
        }
        conexao.execute("VACUUM")
    finally:
        conexao.close()
    for tabela, n in contagens.items():
        print(f"  {tabela}: {n} linhas")
    print(f"Todas as tabelas resumo foram atualizadas com sucesso (SQLite: {caminho.name}).")
    return contagens


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sqlite", nargs="?", const=str(SQLITE_PADRAO), metavar="CAMINHO",
                        help="usa SQLite em vez de MySQL (padrão: data/telecom_crm_.sqlite)")
    args = parser.parse_args()
    if args.sqlite:
        atualizar_tabelas_resumo_sqlite(args.sqlite)
    else:
        atualizar_tabelas_resumo()
