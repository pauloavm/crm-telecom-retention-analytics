import os
import pymysql
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def obter_configuracao_obrigatoria(nome: str) -> str:
    valor = os.getenv(nome)
    if valor is None:
        raise RuntimeError(f"Variável de ambiente obrigatória não definida: {nome}")
    return valor


USUARIO = obter_configuracao_obrigatoria("DB_USUARIO")
SENHA = obter_configuracao_obrigatoria("DB_SENHA")
HOST = obter_configuracao_obrigatoria("DB_HOST")
PORTA = int(os.getenv("DB_PORTA", "3306"))
BANCO_DESTINO = obter_configuracao_obrigatoria("DB_DESTINO")

PASTA_SQL = Path(__file__).resolve().parent / "sql"

ARQUIVOS_SQL = [
    "calc_arpu.sql",
    "cohort_analysis.sql",
    "kpis_mensais.sql",
    "kpi_snapshot_atual.sql"
]


def executar_arquivo_sql(cursor, caminho_arquivo):
    """Le um arquivo .sql e executa cada instrucao separadamente."""
    with open(caminho_arquivo, "r", encoding="utf-8") as arquivo:
        conteudo = arquivo.read()

    comandos = [c.strip() for c in conteudo.split(";") if c.strip()]

    for comando in comandos:
        cursor.execute(comando)


def atualizar_tabelas_resumo():
    """Conecta no MySQL e recria todas as tabelas resumo a partir dos arquivos .sql."""
    conexao = pymysql.connect(
        host=HOST,
        port=PORTA,
        user=USUARIO,
        password=SENHA,
        database=BANCO_DESTINO
    )
    try:
        with conexao.cursor() as cursor:
            for nome_arquivo in ARQUIVOS_SQL:
                caminho = PASTA_SQL / nome_arquivo
                print(f"Executando: {nome_arquivo}")
                executar_arquivo_sql(cursor, caminho)
        conexao.commit()
        print("Todas as tabelas resumo foram atualizadas com sucesso.")
    finally:
        conexao.close()


if __name__ == "__main__":
    atualizar_tabelas_resumo()