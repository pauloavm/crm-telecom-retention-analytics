"""Gera dashboards/dashboard_crm_telecom.xlsx — o dashboard do Streamlit em Excel.

O arquivo é 100% baseado em fórmulas (COUNTIFS/SUMIFS sobre a aba Dados): ao trocar
os filtros da aba Dashboard, KPIs, gráficos e matriz de cohort recalculam sozinhos,
sem macros e sem Power Query. As fórmulas seguem specs/kpis.spec.md.

Uso:
    python build_excel_dashboard.py [--db data/telecom_crm_.sqlite] [--out dashboards/dashboard_crm_telecom.xlsx]
"""
from __future__ import annotations

import argparse
import sqlite3
from datetime import date
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.formatting.rule import ColorScaleRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation

BASE_DIR = Path(__file__).resolve().parent
DB_PADRAO = BASE_DIR / "data" / "telecom_crm_.sqlite"
OUT_PADRAO = BASE_DIR / "dashboards" / "dashboard_crm_telecom.xlsx"

# Paleta do app Streamlit
COBALT, OBSIDIAN, CHALK, WHITE = "0012FF", "111111", "F3F3F3", "FFFFFF"
SLATE, BORDER, AMBER, RED, GREEN = "64748B", "E2E8F0", "F59E0B", "EF4444", "10B981"
FONT = "Arial"
MAX_TENURE = 12

BRL = '"R$" #,##0.00'
BRL0 = '"R$" #,##0'
PCT = "0.0%"
MES = "mmm/yy"


def font(size=10, bold=False, color=OBSIDIAN, italic=False):
    return Font(name=FONT, size=size, bold=bold, color=color, italic=italic)


def fill(hex_color):
    return PatternFill("solid", start_color=hex_color, end_color=hex_color)


def to_date(iso: str) -> date:
    return date.fromisoformat(iso)


def carregar(db: Path):
    conn = sqlite3.connect(db)
    fatos = conn.execute(
        """
        SELECT cm.month_start, cm.customer_id, c.cohort_month, cm.tenure_month, cm.active_flag,
               cm.churn_flag, cm.status, cm.monthly_fee, cm.recognized_revenue, cm.revenue_at_risk,
               cm.days_overdue, c.plan, c.contract_type, c.state
        FROM customer_monthly cm JOIN customers c USING (customer_id)
        ORDER BY cm.month_start, cm.customer_id
        """
    ).fetchall()
    clientes = conn.execute(
        "SELECT customer_id, cohort_month, plan, contract_type, state, current_status FROM customers ORDER BY cohort_month, customer_id"
    ).fetchall()
    meses = [r[0] for r in conn.execute("SELECT DISTINCT month_start FROM customer_monthly ORDER BY 1")]
    listas = {
        col: [r[0] for r in conn.execute(f"SELECT DISTINCT {col} FROM customers ORDER BY 1")]
        for col in ("plan", "contract_type", "state")
    }
    conn.close()
    return fatos, clientes, meses, listas


def tabela(ws, headers, rows, date_cols=(), formats=None):
    """Escreve uma tabela simples com cabeçalho estilizado e congela a 1ª linha."""
    formats = formats or {}
    for j, h in enumerate(headers, 1):
        c = ws.cell(row=1, column=j, value=h)
        c.font = font(bold=True, color=WHITE)
        c.fill = fill(OBSIDIAN)
    for i, row in enumerate(rows, 2):
        for j, v in enumerate(row, 1):
            ws.cell(row=i, column=j, value=to_date(v) if j in date_cols else v)
    for j in range(1, len(headers) + 1):
        letter = get_column_letter(j)
        ws.column_dimensions[letter].width = max(12, len(headers[j - 1]) + 4)
        fmt = MES if j in date_cols else formats.get(j)
        if fmt:
            for i in range(2, len(rows) + 2):
                ws.cell(row=i, column=j).number_format = fmt
    ws.freeze_panes = "A2"


def build(db: Path = DB_PADRAO, out: Path = OUT_PADRAO) -> Path:
    fatos, clientes, meses, listas = carregar(db)
    n_fatos, n_cli, n_meses = len(fatos), len(clientes), len(meses)

    wb = Workbook()
    dash = wb.active
    dash.title = "Dashboard"
    mensal = wb.create_sheet("Mensal")
    dados = wb.create_sheet("Dados")
    cli = wb.create_sheet("Clientes")
    lst = wb.create_sheet("Listas")
    sobre = wb.create_sheet("Sobre")

    # ------------------------------------------------------------------ Dados
    tabela(
        dados,
        ["month_start", "customer_id", "cohort_month", "tenure_month", "active_flag", "churn_flag", "status",
         "monthly_fee", "recognized_revenue", "revenue_at_risk", "days_overdue", "plan", "contract_type", "state"],
        fatos, date_cols=(1, 3), formats={8: BRL, 9: BRL, 10: BRL},
    )
    dados.column_dimensions["B"].width = 38
    last = n_fatos + 1

    def rng(col):  # coluna da aba Dados como intervalo absoluto
        return f"Dados!${col}$2:${col}${last}"

    names = {
        "d_mes": rng("A"), "d_safra": rng("C"), "d_tenure": rng("D"), "d_ativo": rng("E"), "d_status": rng("G"),
        "d_mensalidade": rng("H"), "d_receita": rng("I"), "d_risco": rng("J"), "d_plano": rng("L"),
        "d_contrato": rng("M"), "d_uf": rng("N"),
    }

    # ---------------------------------------------------------------- Clientes
    tabela(cli, ["customer_id", "cohort_month", "plan", "contract_type", "state", "current_status"],
           clientes, date_cols=(2,))
    cli.column_dimensions["A"].width = 38
    lc = n_cli + 1
    names.update({
        "c_safra": f"Clientes!$B$2:$B${lc}", "c_plano": f"Clientes!$C$2:$C${lc}",
        "c_contrato": f"Clientes!$D$2:$D${lc}", "c_uf": f"Clientes!$E$2:$E${lc}",
    })

    # ------------------------------------------------------------------ Listas
    colunas = [("Plano", ["Todos"] + listas["plan"]), ("Contrato", ["Todos"] + listas["contract_type"]),
               ("UF", ["Todos"] + listas["state"]), ("Mês", meses)]
    for j, (titulo, valores) in enumerate(colunas, 1):
        lst.cell(row=1, column=j, value=titulo).font = font(bold=True)
        for i, v in enumerate(valores, 2):
            c = lst.cell(row=i, column=j, value=to_date(v) if titulo == "Mês" else v)
            if titulo == "Mês":
                c.number_format = MES
        lst.column_dimensions[get_column_letter(j)].width = 18
    names.update({
        "lista_plano": f"Listas!$A$2:$A${len(colunas[0][1]) + 1}",
        "lista_contrato": f"Listas!$B$2:$B${len(colunas[1][1]) + 1}",
        "lista_uf": f"Listas!$C$2:$C${len(colunas[2][1]) + 1}",
        "lista_meses": f"Listas!$D$2:$D${n_meses + 1}",
    })

    # --------------------------------------------------------------- Dashboard
    dash.sheet_view.showGridLines = False
    dash.sheet_properties.tabColor = COBALT
    for col in range(1, 20):
        dash.column_dimensions[get_column_letter(col)].width = 10.5
    dash.column_dimensions["A"].width = 2.5

    # Cabeçalho
    for r in range(2, 6):
        for c in range(2, 19):
            dash.cell(row=r, column=c).fill = fill(OBSIDIAN)
    dash["B2"] = "SP TELECOM — INTELIGÊNCIA EM CONECTIVIDADE"
    dash["B2"].font = font(8, True, WHITE)
    dash["B3"] = "Telecom CRM & Retention Dashboard"
    dash["B3"].font = font(20, True, WHITE)
    dash["B4"] = "Acompanhamento executivo de receita, ARPU, inadimplência em Grace Period e matriz de safras."
    dash["B4"].font = font(9, color="CBD5E1")
    dash["N3"] = "Fonte: data/telecom_crm_.sqlite (dados sintéticos)"
    dash["N3"].font = font(8, color="CBD5E1", italic=True)
    for c in range(14, 19):
        dash.cell(row=5, column=c).fill = fill(COBALT)
    dash.row_dimensions[3].height = 30

    # Filtros (células editáveis em amarelo claro)
    dash["B6"] = "🎛️ Filtros — altere as células em amarelo"
    dash["B6"].font = font(11, True)
    # (coluna inicial, rótulo, coluna final da caixa, valor padrão, lista de opções)
    filtros = [("B", "Plano do Cliente", "D", "Todos", "lista_plano"),
               ("F", "Tipo de Contrato", "H", "Todos", "lista_contrato"),
               ("J", "Estado (UF)", "K", "Todos", "lista_uf"),
               ("M", "Início da Janela", "N", to_date(meses[0]), "lista_meses"),
               ("P", "Fim da Janela", "Q", to_date(meses[-1]), "lista_meses")]
    input_border = Border(*(Side(style="thin", color=COBALT),) * 4)
    for cell_col, label, end_col, default, lista in filtros:
        dash[f"{cell_col}7"] = label
        dash[f"{cell_col}7"].font = font(9, True, SLATE)
        for col in range(dash[f"{cell_col}8"].column, dash[f"{end_col}8"].column + 1):
            box = dash.cell(row=8, column=col)
            box.fill = fill("FFF7CC")
            box.border = input_border
        dash.merge_cells(f"{cell_col}8:{end_col}8")
        c = dash[f"{cell_col}8"]
        c.value = default
        c.fill = fill("FFF7CC")
        c.font = font(10, True)
        c.border = input_border
        c.alignment = Alignment(horizontal="center")
        if isinstance(default, date):
            c.number_format = MES
        dv = DataValidation(type="list", formula1=f"={lista}", allow_blank=False, showErrorMessage=True,
                            errorTitle="Valor inválido", error="Escolha um valor da lista.")
        dash.add_data_validation(dv)
        dv.add(c)
    dash["B9"] = '=IF(f_inicio>f_fim,"⚠ O mês de início é posterior ao mês de fim: ajuste a janela.","")'
    dash["B9"].font = font(9, True, RED)

    names.update({"f_plano": "Dashboard!$B$8", "f_contrato": "Dashboard!$F$8", "f_uf": "Dashboard!$J$8",
                  "f_inicio": "Dashboard!$M$8", "f_fim": "Dashboard!$P$8"})

    # ------------------------------------------------------------------ Mensal
    mensal.sheet_properties.tabColor = OBSIDIAN
    mensal["A1"] = "Critério plano"
    mensal["B1"] = '=IF(f_plano="Todos","*",f_plano)'
    mensal["C1"] = "Critério contrato"
    mensal["D1"] = '=IF(f_contrato="Todos","*",f_contrato)'
    mensal["E1"] = "Critério UF"
    mensal["F1"] = '=IF(f_uf="Todos","*",f_uf)'
    for ref in ("A1", "C1", "E1"):
        mensal[ref].font = font(8, color=SLATE)
    names.update({"k_plano": "Mensal!$B$1", "k_contrato": "Mensal!$D$1", "k_uf": "Mensal!$F$1"})

    cab = ["#", "Mês de Referência", "Clientes Ativos", "Ativos Saudáveis", "Grace Period", "Cancelamentos",
           "Base do Mês", "Receita Reconhecida (R$)", "Receita sob Risco (R$)", "Receita Perdida - Churn (R$)",
           "ARPU (R$)", "Churn Rate (%)"]
    for j, h in enumerate(cab, 1):
        c = mensal.cell(row=3, column=j, value=h)
        c.font = font(9, True, WHITE)
        c.fill = fill(OBSIDIAN)
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        mensal.column_dimensions[get_column_letter(j)].width = 15
    mensal.column_dimensions["A"].width = 5
    mensal.row_dimensions[3].height = 32
    mensal.freeze_panes = "C4"

    filt = "d_plano,k_plano,d_contrato,k_contrato,d_uf,k_uf"
    first_row = 4
    for i in range(n_meses):
        r = first_row + i
        mensal[f"A{r}"] = i + 1
        mensal[f"B{r}"] = f'=IF(EDATE(f_inicio,A{r}-1)<=f_fim,EDATE(f_inicio,A{r}-1),"")'
        mensal[f"B{r}"].number_format = MES
        cond = f'IF($B{r}="",NA(),'
        mensal[f"C{r}"] = f"={cond}COUNTIFS(d_mes,$B{r},d_ativo,1,{filt}))"
        mensal[f"D{r}"] = f'={cond}COUNTIFS(d_mes,$B{r},d_status,"ACTIVE",{filt}))'
        mensal[f"E{r}"] = f'={cond}COUNTIFS(d_mes,$B{r},d_status,"GRACE_PERIOD",{filt}))'
        mensal[f"F{r}"] = f'={cond}COUNTIFS(d_mes,$B{r},d_status,"CHURN",{filt}))'
        mensal[f"G{r}"] = f"={cond}COUNTIFS(d_mes,$B{r},{filt}))"
        mensal[f"H{r}"] = f"={cond}SUMIFS(d_receita,d_mes,$B{r},{filt}))"
        mensal[f"I{r}"] = f'={cond}SUMIFS(d_risco,d_mes,$B{r},d_status,"GRACE_PERIOD",{filt}))'
        mensal[f"J{r}"] = f'={cond}SUMIFS(d_mensalidade,d_mes,$B{r},d_status,"CHURN",{filt}))'
        mensal[f"K{r}"] = f"={cond}IF(C{r}>0,H{r}/C{r},0))"
        mensal[f"L{r}"] = f"={cond}IF(G{r}>0,F{r}/G{r},0))"
        for col, fmt in zip("CDEFGHIJKL", ["#,##0"] * 5 + [BRL] * 4 + [PCT]):
            mensal[f"{col}{r}"].number_format = fmt
            mensal[f"{col}{r}"].font = font(9)
        mensal[f"A{r}"].font = font(9, color=SLATE)
        mensal[f"B{r}"].font = font(9, True)
    last_m = first_row + n_meses - 1
    nota = last_m + 2
    mensal[f"A{nota}"] = ("Linhas vazias = meses fora da janela selecionada (ficam fora dos gráficos). "
                          "Fórmulas: specs/kpis.spec.md (KPI-01 a KPI-07).")
    # Meses fora da janela retornam NA() de propósito (lacuna nos gráficos); a fonte branca os esconde.
    mensal.conditional_formatting.add(
        f"C{first_row}:L{last_m}", FormulaRule(formula=[f"ISNA(C{first_row})"], font=Font(name=FONT, color=WHITE))
    )
    mensal[f"A{nota}"].font = font(8, color=SLATE, italic=True)

    def col_m(col):
        return f"Mensal!${col}${first_row}:${col}${last_m}"

    # Linha do último mês da janela e do mês anterior
    names.update({
        "m_linha_fim": f"MATCH(f_fim,{col_m('B')},0)",
    })

    # KPI cards
    cards = [
        ("B", "CLIENTES ATIVOS NA BASE", "C", "#,##0"),
        ("F", "ARPU MÉDIO ATUAL", "K", BRL),
        ("J", "TAXA DE CHURN ATUAL", "L", '0.00%'),
        ("N", "RECEITA SOB RISCO (GRACE)", "I", BRL),
    ]
    subs = {
        "B": None,  # variação vs mês anterior (fórmula abaixo)
        "F": "Receita média por usuário ativo",
        "J": "Cancelados / base do mês",
        "N": "Atraso de 1 a 15 dias (recuperável)",
    }
    card_border = Side(style="thin", color=BORDER)
    for start_col, titulo, src, fmt in cards:
        c0 = dash[f"{start_col}11"].column
        cols = [get_column_letter(c0 + k) for k in range(4 if start_col != "N" else 4)]
        for r in range(11, 16):
            for k, col in enumerate(cols):
                cell = dash[f"{col}{r}"]
                cell.fill = fill(WHITE if r < 15 else COBALT)
                cell.border = Border(top=card_border if r == 11 else None, left=card_border if k == 0 else None,
                                     right=card_border if k == len(cols) - 1 else None)
        dash.row_dimensions[15].height = 4
        for r in (11, 12, 13, 14):
            dash.merge_cells(f"{cols[0]}{r}:{cols[-1]}{r}")
        dash[f"{start_col}11"] = titulo
        dash[f"{start_col}11"].font = font(8, True, SLATE)
        dash[f"{start_col}12"] = f'=IF(f_inicio>f_fim,0,INDEX({col_m(src)},m_linha_fim))'
        dash[f"{start_col}12"].number_format = fmt
        dash[f"{start_col}12"].font = font(20, True, RED if start_col == "N" else OBSIDIAN)
        dash[f"{start_col}12"].alignment = Alignment(horizontal="left")
        dash.row_dimensions[12].height = 32
        sub = subs[start_col]
        if sub:
            dash[f"{start_col}13"] = sub
            dash[f"{start_col}13"].font = font(8, color=SLATE)
        dash[f"{start_col}14"] = "=f_fim"
        dash[f"{start_col}14"].number_format = '"Mês de referência: "mmm/yy'
        dash[f"{start_col}14"].font = font(8, color=SLATE, italic=True)
        dash[f"{start_col}14"].alignment = Alignment(horizontal="left")

    # Variação de clientes ativos vs mês anterior (0% quando a janela tem 1 mês)
    dash["B13"] = (f"=IF(f_inicio>f_fim,0,IFERROR(INDEX({col_m('C')},m_linha_fim)/"
                   f"INDEX({col_m('C')},MATCH(EDATE(f_fim,-1),{col_m('B')},0))-1,0))")
    dash["B13"].number_format = '"▲ "0.0%" vs mês anterior";"▼ "0.0%" vs mês anterior";"= 0.0% vs mês anterior"'
    dash["B13"].font = font(8, True, GREEN)
    dash["B13"].alignment = Alignment(horizontal="left")
    dash.conditional_formatting.add("B13", FormulaRule(formula=["$B$13<0"], font=Font(name=FONT, color=RED, bold=True)))
    dash.conditional_formatting.add("J12", FormulaRule(formula=["$J$12>0.08"], font=Font(name=FONT, color=RED, bold=True, size=20)))

    # Gráfico 1: Faturamento (barras) x ARPU (linha, eixo secundário)
    cats = Reference(mensal, min_col=2, min_row=first_row, max_row=last_m)
    bar = BarChart()
    bar.type = "col"
    bar.title = "Evolução Financeira: Faturamento vs. ARPU"
    bar.add_data(Reference(mensal, min_col=8, min_row=3, max_row=last_m), titles_from_data=True)
    bar.set_categories(cats)
    bar.y_axis.title = "Faturamento (R$)"
    bar.y_axis.number_format = BRL0
    bar.y_axis.majorGridlines = None
    bar.series[0].graphicalProperties.solidFill = COBALT
    bar.series[0].graphicalProperties.line.solidFill = COBALT
    bar.gapWidth = 40
    line = LineChart()
    line.add_data(Reference(mensal, min_col=11, min_row=3, max_row=last_m), titles_from_data=True)
    line.y_axis.axId = 200
    line.y_axis.title = "ARPU (R$)"
    line.y_axis.number_format = BRL0
    line.y_axis.crosses = "max"
    line.series[0].graphicalProperties.line.solidFill = OBSIDIAN
    line.series[0].graphicalProperties.line.width = 28000
    line.series[0].smooth = False
    bar += line
    for ax in (bar.x_axis, bar.y_axis, line.y_axis):
        ax.delete = False
    bar.x_axis.number_format = MES
    bar.legend.position = "b"
    bar.height, bar.width = 8.5, 17
    dash.add_chart(bar, "B18")

    # Gráfico 2: Composição da base (barras empilhadas)
    comp = BarChart()
    comp.type = "col"
    comp.grouping = "stacked"
    comp.overlap = 100
    comp.title = "Composição da Base de Clientes"
    for col, color in ((4, COBALT), (5, AMBER), (6, RED)):
        comp.add_data(Reference(mensal, min_col=col, min_row=3, max_row=last_m), titles_from_data=True)
        s = comp.series[-1]
        s.graphicalProperties.solidFill = color
        s.graphicalProperties.line.solidFill = color
    comp.set_categories(cats)
    comp.gapWidth = 40
    comp.x_axis.number_format = MES
    for ax in (comp.x_axis, comp.y_axis):
        ax.delete = False
    comp.legend.position = "b"
    comp.height, comp.width = 8.5, 13.5
    dash.add_chart(comp, "K18")

    # Matriz de cohort
    top = 36
    dash[f"B{top}"] = "🧊 Matriz Térmica de Cohort (Retenção por Safra)"
    dash[f"B{top}"].font = font(13, True)
    dash[f"B{top + 1}"] = ("Percentual de clientes ativos em relação ao total adquirido na safra "
                           "(M0 = mês de entrada) · respeita filtros e janela · KPI-08")
    dash[f"B{top + 1}"].font = font(8, color=SLATE, italic=True)
    hdr = top + 3
    dash[f"B{hdr}"] = "Safra"
    dash[f"C{hdr}"] = "Clientes"
    for t in range(MAX_TENURE + 1):
        dash.cell(row=hdr, column=4 + t, value=f"M{t}")
    for c in range(2, 5 + MAX_TENURE):
        cell = dash.cell(row=hdr, column=c)
        cell.font = font(9, True, WHITE)
        cell.fill = fill(OBSIDIAN)
        cell.alignment = Alignment(horizontal="center")
    names["ultimo_mes_dados"] = f"Listas!$D${n_meses + 1}"
    for i in range(n_meses):
        r = hdr + 1 + i
        dash[f"B{r}"] = f"=INDEX(lista_meses,{i + 1})"
        dash[f"B{r}"].number_format = MES
        dash[f"B{r}"].font = font(9, True)
        dash[f"B{r}"].alignment = Alignment(horizontal="center")
        dash[f"C{r}"] = f"=COUNTIFS(c_safra,$B{r},c_plano,k_plano,c_contrato,k_contrato,c_uf,k_uf)"
        dash[f"C{r}"].font = font(9, color=SLATE)
        dash[f"C{r}"].alignment = Alignment(horizontal="center")
        for t in range(MAX_TENURE + 1):
            col = get_column_letter(4 + t)
            mes_ref = f"EDATE($B{r},{t})"
            dash[f"{col}{r}"] = (
                f'=IF(OR($C{r}=0,{mes_ref}<f_inicio,{mes_ref}>f_fim,{mes_ref}>ultimo_mes_dados),"",'
                f"COUNTIFS(d_safra,$B{r},d_tenure,{t},d_ativo,1,{filt})/$C{r})"
            )
            dash[f"{col}{r}"].number_format = "0.0%"
            dash[f"{col}{r}"].font = font(8)
            dash[f"{col}{r}"].alignment = Alignment(horizontal="center")
    last_c = hdr + n_meses
    area = f"D{hdr + 1}:{get_column_letter(4 + MAX_TENURE)}{last_c}"
    dash.conditional_formatting.add(area, ColorScaleRule(start_type="num", start_value=0, start_color="EFF6FF",
                                                          mid_type="num", mid_value=0.5, mid_color="60A5FA",
                                                          end_type="num", end_value=1, end_color=COBALT))
    dash.conditional_formatting.add(area, FormulaRule(formula=["AND(ISNUMBER(D%d),D%d>=0.6)" % (hdr + 1, hdr + 1)],
                                                      font=Font(name=FONT, color=WHITE, size=8)))
    rodape = last_c + 2
    dash[f"B{rodape}"] = ("⚠️ Nota de isenção: todos os dados, nomes e valores são estritamente fictícios, gerados por "
                          "modelo sintético para fins de portfólio. Gerado por build_excel_dashboard.py.")
    dash[f"B{rodape}"].font = font(8, color=SLATE, italic=True)
    dash.freeze_panes = "A10"

    # -------------------------------------------------------------------- Sobre
    sobre.sheet_view.showGridLines = False
    sobre.column_dimensions["A"].width = 3
    sobre.column_dimensions["B"].width = 34
    sobre.column_dimensions["C"].width = 100
    linhas = [
        ("Telecom CRM & Retention — Dashboard em Excel", None),
        ("", None),
        ("Como usar", "Na aba Dashboard, altere as células amarelas (Plano, Contrato, UF, Início e Fim). Tudo recalcula sozinho."),
        ("Abas", "Dashboard (visão executiva) · Mensal (série consolidada) · Dados (fato mensal por cliente) · "
                 "Clientes (dimensão) · Listas (opções dos filtros)."),
        ("Tecnologia", "Somente fórmulas nativas (COUNTIFS, SUMIFS, INDEX/MATCH, EDATE). Sem macros, sem Power Query."),
        ("Origem", f"data/telecom_crm_.sqlite · {n_cli:,} clientes · {n_fatos:,} registros mensais · "
                   f"{meses[0][:7]} a {meses[-1][:7]}".replace(",", ".")),
        ("Reprodução", "python build_excel_dashboard.py  (o mesmo cálculo do app Streamlit — analytics.py)"),
        ("", None),
        ("Definições (specs/kpis.spec.md)", None),
        ("KPI-01 Clientes ativos", "Clientes com active_flag = 1 no mês (inclui Grace Period)."),
        ("KPI-02 Ativos saudáveis", "Clientes com status ACTIVE. Saudáveis + Grace = Ativos."),
        ("KPI-03 Receita reconhecida", "Soma de recognized_revenue."),
        ("KPI-04 ARPU", "Receita reconhecida ÷ clientes ativos."),
        ("KPI-05 Churn rate", "Cancelamentos do mês ÷ base do mês (ativos + cancelados)."),
        ("KPI-06 Receita sob risco", "Mensalidade de clientes em GRACE_PERIOD (atraso de 1 a 15 dias). Cancelados não entram."),
        ("KPI-07 Receita perdida", "Mensalidade de clientes que cancelaram no mês."),
        ("KPI-08 Retenção de safra", "Ativos da safra no tenure ÷ total de clientes adquiridos na safra."),
        ("", None),
        ("Aviso", "Dados 100% sintéticos (Faker). Empresa, clientes e valores são fictícios."),
    ]
    for i, (k, v) in enumerate(linhas, 2):
        sobre[f"B{i}"] = k
        sobre[f"B{i}"].font = font(16 if i == 2 else 10, bold=True, color=COBALT if i == 2 or v is None else OBSIDIAN)
        if v:
            sobre[f"C{i}"] = v
            sobre[f"C{i}"].font = font(10)
            sobre[f"C{i}"].alignment = Alignment(wrap_text=True, vertical="top")

    # Nomes definidos (deixam as fórmulas legíveis)
    for name, ref in names.items():
        wb.defined_names[name] = DefinedName(name, attr_text=ref)

    for ws in (mensal, dados, cli, lst):
        ws.sheet_view.zoomScale = 90
    lst.sheet_state = "hidden"
    wb.calculation.fullCalcOnLoad = True
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", type=Path, default=DB_PADRAO)
    ap.add_argument("--out", type=Path, default=OUT_PADRAO)
    args = ap.parse_args()
    print(f"Dashboard gerado: {build(args.db, args.out)}")
