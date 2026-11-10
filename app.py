import sqlite3
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analytics import Filters, cohort_retention, find_database, headline, monthly_kpis

st.set_page_config(
    page_title="SP Telecom — CRM & Retention Analytics",
    page_icon="📶",
    layout="wide",
    initial_sidebar_state="auto"
)

SURF_THEME = {
    "cobalt_blue": "#0012FF",
    "obsidian_black": "#111111",
    "chalk_white": "#F3F3F3",
    "pure_white": "#FFFFFF",
    "sky_blue": "#3B82F6",
    "cyan_glow": "#00D2FF",
    "slate_dark": "#1E293B",
    "slate_gray": "#64748B",
    "card_border": "#E2E8F0",
    "good_green": "#10B981",
    "warning_amber": "#F59E0B",
    "danger_red": "#EF4444",
    "cohort_min": "#EFF6FF",
    "cohort_mid": "#60A5FA",
    "cohort_max": "#0012FF"
}

# Injecting Custom CSS matching Surf Telecom Brandbook
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700;900&display=swap');
        
        html, body, [class*="css"] {{
            font-family: 'Roboto', sans-serif;
            background-color: {SURF_THEME['chalk_white']};
            color: {SURF_THEME['obsidian_black']};
        }}
        
        .main-header {{
            background: linear-gradient(135deg, {SURF_THEME['obsidian_black']} 0%, #0a0e27 60%, {SURF_THEME['cobalt_blue']} 100%);
            border-radius: 12px;
            padding: 24px 30px;
            color: {SURF_THEME['pure_white']};
            margin-bottom: 24px;
            box-shadow: 0 4px 20px rgba(0, 18, 255, 0.15);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .brand-badge {{
            background: {SURF_THEME['cobalt_blue']};
            color: {SURF_THEME['pure_white']};
            font-weight: 700;
            padding: 4px 12px;
            border-radius: 6px;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}
        
        .metric-card {{
            background: {SURF_THEME['pure_white']};
            border-radius: 12px;
            border: 1px solid {SURF_THEME['card_border']};
            padding: 18px 22px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            position: relative;
            overflow: hidden;
        }}
        
        .metric-card::after {{
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: {SURF_THEME['cobalt_blue']};
        }}
        
        .metric-title {{
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: {SURF_THEME['slate_gray']};
            margin-bottom: 6px;
        }}
        
        .metric-value {{
            font-size: 1.85rem;
            font-weight: 900;
            color: {SURF_THEME['obsidian_black']};
            line-height: 1.2;
        }}
        
        .metric-sub {{
            font-size: 0.75rem;
            color: {SURF_THEME['slate_gray']};
            margin-top: 6px;
        }}
        
        /* Streamlit widget tweaks */
        .stSelectbox label, .stMultiSelect label {{
            font-weight: 600;
            font-size: 0.85rem;
            color: {SURF_THEME['obsidian_black']};
        }}
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_database_connection():
    """Localiza o SQLite relativo ao repositório (independe do cwd) ou gera um fallback sintético."""
    db_file = find_database()
    if db_file:
        conn = sqlite3.connect(db_file, check_same_thread=False)
        return conn, False
    
    # Fallback in-memory generator if SQLite file not present
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    _generate_sample_sqlite_database(conn)
    return conn, True

def _generate_sample_sqlite_database(conn):
    """Creates realistic demo schema and data matching project requirements."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE customers (
            customer_id TEXT PRIMARY KEY,
            full_name TEXT,
            city TEXT,
            state TEXT,
            plan TEXT,
            contract_type TEXT,
            cohort_month TEXT,
            monthly_fee REAL,
            current_status TEXT
        );
    """)
    cursor.execute("""
        CREATE TABLE customer_monthly (
            monthly_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT,
            month_start TEXT,
            tenure_month INTEGER,
            active_flag INTEGER,
            churn_flag INTEGER,
            status TEXT,
            monthly_fee REAL,
            recognized_revenue REAL,
            revenue_at_risk REAL,
            days_overdue INTEGER
        );
    """)
    
    np.random.seed(42)
    plans = [("Controle 10GB", 49.9), ("Controle 20GB", 69.9), ("Pós-pago 30GB", 89.9), ("Pós-pago 50GB", 119.9), ("Pós-pago 100GB", 169.9)]
    contracts = ["Monthly", "One year", "Two year"]
    states = ["SP", "RJ", "MG", "BA", "PR", "RS", "PE", "SC", "GO", "DF"]
    
    dates = pd.date_range("2024-01-01", "2025-12-01", freq="MS").strftime("%Y-%m-%d").tolist()
    
    cust_rows = []
    monthly_rows = []
    
    for i in range(1, 3501):
        c_id = f"cust_{i:05d}"
        plan_name, fee = plans[np.random.choice(len(plans), p=[0.35, 0.30, 0.18, 0.12, 0.05])]
        c_type = np.random.choice(contracts, p=[0.45, 0.40, 0.15])
        st_val = np.random.choice(states)
        cohort_idx = np.random.randint(0, len(dates) - 1)
        cohort_m = dates[cohort_idx]
        
        churn_tenure = 999
        if np.random.rand() < 0.28:
            churn_tenure = np.random.choice([1, 2, 3, 4, 6, 8], p=[0.10, 0.25, 0.35, 0.15, 0.10, 0.05])
            
        cur_status = "CHURN" if churn_tenure < (len(dates) - cohort_idx) else "ACTIVE"
        cust_rows.append((c_id, f"Cliente {i}", "São Paulo", st_val, plan_name, c_type, cohort_m, fee, cur_status))
        
        tenure = 0
        for m_idx in range(cohort_idx, len(dates)):
            m_date = dates[m_idx]
            if tenure == churn_tenure:
                monthly_rows.append((c_id, m_date, tenure, 0, 1, "CHURN", fee, 0.0, fee, 0))
                break
            elif tenure > churn_tenure:
                break
            else:
                # Grace period possibility
                is_grace = (np.random.rand() < 0.06)
                status_str = "GRACE_PERIOD" if is_grace else "ACTIVE"
                rev_risk = fee if is_grace else 0.0
                monthly_rows.append((c_id, m_date, tenure, 1, 0, status_str, fee, fee, rev_risk, 5 if is_grace else 0))
            tenure += 1
            
    cursor.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?,?,?,?)", cust_rows)
    cursor.executemany("""
        INSERT INTO customer_monthly (customer_id, month_start, tenure_month, active_flag, churn_flag, status, monthly_fee, recognized_revenue, revenue_at_risk, days_overdue)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, monthly_rows)
    conn.commit()

conn, is_fallback = get_database_connection()

@st.cache_data(ttl=600)
def load_filter_options():
    plans = pd.read_sql_query("SELECT DISTINCT plan FROM customers WHERE plan IS NOT NULL ORDER BY plan;", conn)['plan'].tolist()
    contracts = pd.read_sql_query("SELECT DISTINCT contract_type FROM customers WHERE contract_type IS NOT NULL ORDER BY contract_type;", conn)['contract_type'].tolist()
    states = pd.read_sql_query("SELECT DISTINCT state FROM customers WHERE state IS NOT NULL ORDER BY state;", conn)['state'].tolist()
    months = pd.read_sql_query("SELECT DISTINCT month_start FROM customer_monthly ORDER BY month_start;", conn)['month_start'].tolist()
    return plans, contracts, states, months

plans_list, contracts_list, states_list, months_list = load_filter_options()

with st.sidebar:
    st.markdown(f"""
        <div style="text-align: center; padding: 10px 0 20px 0;">
            <div style="font-size: 1.8rem; font-weight: 900; letter-spacing: -1px; color: {SURF_THEME['cobalt_blue']};">
                SP <span style="color: {SURF_THEME['obsidian_black']};">TELECOM</span>
            </div>
            <div style="font-size: 0.72rem; color: {SURF_THEME['slate_gray']}; font-weight: 500; letter-spacing: 0.05em;">
                PLATAFORMA DE INTELIGÊNCIA & CRM
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🎛️ Filtros Estratégicos")
    
    selected_plans = st.multiselect("Plano do Cliente", options=plans_list, default=[])
    selected_contracts = st.multiselect("Tipo de Contrato", options=contracts_list, default=[])
    selected_states = st.multiselect("Estado (UF)", options=states_list, default=[])
    
    st.divider()
    
    # Timeline range filter
    if len(months_list) > 1:
        month_range = st.select_slider(
            "Janela de Análise",
            options=months_list,
            value=(months_list[0], months_list[-1])
        )
    else:
        month_range = (months_list[0], months_list[0]) if months_list else (None, None)
        
    st.markdown(f"""
        <div style="margin-top: 25px; padding: 12px; background: {SURF_THEME['pure_white']}; border-radius: 8px; border: 1px solid {SURF_THEME['card_border']};">
            <div style="font-size: 0.75rem; font-weight: 700; color: {SURF_THEME['cobalt_blue']};">IDENTIDADE VISUAL APLICADA</div>
            <div style="font-size: 0.7rem; color: {SURF_THEME['slate_gray']}; margin-top: 4px;">
                Paleta: Cobalt Blue (#0012FF), Obsidian Black (#111111), Chalk White (#F3F3F3).
            </div>
        </div>
    """, unsafe_allow_html=True)

filters = Filters(
    plans=tuple(selected_plans),
    contracts=tuple(selected_contracts),
    states=tuple(selected_states),
    month_start=month_range[0],
    month_end=month_range[1],
)


@st.cache_data(ttl=300)
def query_dashboard_data(f: Filters):
    """KPIs mensais e matriz de cohort — fórmulas em analytics.py / specs/kpis.spec.md."""
    return monthly_kpis(conn, f), cohort_retention(conn, f)


df_monthly, cohort_matrix = query_dashboard_data(filters)

st.markdown(f"""
    <div class="main-header">
        <div>
            <div class="brand-badge">SP Telecom — Inteligência em Conectividade</div>
            <h1 style="margin: 8px 0 4px 0; font-size: 1.8rem; font-weight: 800; letter-spacing: -0.5px;">
                Telecom CRM & Retention Dashboard
            </h1>
            <p style="margin: 0; opacity: 0.85; font-size: 0.85rem;">
                Acompanhamento executivo de receita, ARPU, inadimplência em Grace Period e matriz de safras.
            </p>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 0.75rem; text-transform: uppercase; color: #cbd5e1;">Base de Conexão</div>
            <div style="font-weight: 700; font-size: 0.95rem; color: #FFFFFF;">
                {'SQLite Demo Fallback' if is_fallback else 'telecom_crm_.sqlite'}
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

kpis = headline(df_monthly)
cur_active, active_diff_pct = kpis["active"], kpis["active_delta_pct"]
cur_arpu, cur_churn, cur_risk = kpis["arpu"], kpis["churn_rate"], kpis["revenue_at_risk"]
ref_month = kpis["month"] or "—"

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Clientes Ativos na Base</div>
            <div class="metric-value">{cur_active:,.0f}</div>
            <div class="metric-sub" style="color: {'#10B981' if active_diff_pct >= 0 else '#EF4444'};">
                {'▲' if active_diff_pct >= 0 else '▼'} {abs(active_diff_pct):.1f}% vs mês anterior
            </div>
        </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">ARPU Médio Atual</div>
            <div class="metric-value">R$ {cur_arpu:,.2f}</div>
            <div class="metric-sub">Receita média por usuário ativo ({ref_month})</div>
        </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Taxa de Churn Atual</div>
            <div class="metric-value" style="color: {'#EF4444' if cur_churn > 8 else '#111111'};">{cur_churn:.2f}%</div>
            <div class="metric-sub">Cancelados / base do mês ({ref_month})</div>
        </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Receita sob Risco (Grace)</div>
            <div class="metric-value" style="color: #EF4444;">R$ {cur_risk:,.2f}</div>
            <div class="metric-sub">Atraso de 1 a 15 dias (recuperável)</div>
        </div>
    """, unsafe_allow_html=True)

st.write("")

col_left, col_right = st.columns([7, 5])

with col_left:
    st.markdown("#### 📈 Evolução Financeira: Faturamento vs. ARPU")
    if not df_monthly.empty:
        fig_fin = make_subplots(specs=[[{"secondary_y": True}]])
        
        # Revenue bar
        fig_fin.add_trace(
            go.Bar(
                x=df_monthly['month_start'],
                y=df_monthly['total_revenue'],
                name="Faturamento Total (R$)",
                marker_color=SURF_THEME['cobalt_blue'],
                opacity=0.88,
                hovertemplate="<b>Mês:</b> %{x}<br><b>Receita:</b> R$ %{y:,.2f}<extra></extra>"
            ),
            secondary_y=False
        )
        
        # ARPU Line
        fig_fin.add_trace(
            go.Scatter(
                x=df_monthly['month_start'],
                y=df_monthly['arpu'],
                name="ARPU (R$)",
                mode="lines+markers",
                line=dict(color=SURF_THEME['obsidian_black'], width=3),
                marker=dict(size=6, color=SURF_THEME['obsidian_black']),
                hovertemplate="<b>Mês:</b> %{x}<br><b>ARPU:</b> R$ %{y:,.2f}<extra></extra>"
            ),
            secondary_y=True
        )
        
        fig_fin.update_layout(
            plot_bgcolor=SURF_THEME['pure_white'],
            paper_bgcolor=SURF_THEME['pure_white'],
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            font=dict(family="Roboto", color=SURF_THEME['obsidian_black'])
        )
        fig_fin.update_xaxes(showgrid=False, linecolor=SURF_THEME['card_border'])
        fig_fin.update_yaxes(title_text="Faturamento (R$)", showgrid=True, gridcolor="#F1F5F9", secondary_y=False)
        fig_fin.update_yaxes(title_text="ARPU (R$)", showgrid=False, secondary_y=True)
        st.plotly_chart(fig_fin, width="stretch")
    else:
        st.info("Nenhum dado encontrado para os filtros selecionados.")

with col_right:
    st.markdown("#### 👥 Composição da Base de Clientes")
    if not df_monthly.empty:
        fig_comp = go.Figure()
        
        fig_comp.add_trace(go.Bar(
            x=df_monthly['month_start'],
            y=df_monthly['healthy_customers'],
            name="Ativos Saudáveis",
            marker_color=SURF_THEME['cobalt_blue']
        ))
        
        fig_comp.add_trace(go.Bar(
            x=df_monthly['month_start'],
            y=df_monthly['grace_customers'],
            name="Grace Period (Inadimplentes)",
            marker_color=SURF_THEME['warning_amber']
        ))
        
        fig_comp.add_trace(go.Bar(
            x=df_monthly['month_start'],
            y=df_monthly['churn_customers'],
            name="Cancelados (Churn)",
            marker_color=SURF_THEME['danger_red']
        ))
        
        fig_comp.update_layout(
            barmode='stack',
            plot_bgcolor=SURF_THEME['pure_white'],
            paper_bgcolor=SURF_THEME['pure_white'],
            margin=dict(l=20, r=20, t=30, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            font=dict(family="Roboto", color=SURF_THEME['obsidian_black'])
        )
        fig_comp.update_xaxes(showgrid=False, linecolor=SURF_THEME['card_border'])
        fig_comp.update_yaxes(showgrid=True, gridcolor="#F1F5F9")
        st.plotly_chart(fig_comp, width="stretch")
    else:
        st.info("Nenhum dado disponível.")

st.markdown("#### 🧊 Matriz Térmica de Cohort (Retenção por Safra)")
st.markdown(
    "<span style='color: #64748B; font-size: 0.82rem;'>Percentual de clientes ativos em relação ao total adquirido na safra (M0 = mês de entrada).</span>",
    unsafe_allow_html=True
)

if not cohort_matrix.empty:
    # Retenção sobre o tamanho total da safra (KPI-08) — não re-baseia safras anteriores à janela
    cohort_display = cohort_matrix.round(1)

    z_values = cohort_display.values
    x_labels = [f"M{c}" for c in cohort_display.columns]
    y_labels = cohort_display.index.tolist()
    
    # Create customized Heatmap matching theme colors
    fig_cohort = go.Figure(data=go.Heatmap(
        z=z_values,
        x=x_labels,
        y=y_labels,
        text=[[f"{val:.1f}%" if not np.isnan(val) else "" for val in row] for row in z_values],
        texttemplate="%{text}",
        colorscale=[
            [0.0, SURF_THEME['cohort_min']],
            [0.5, SURF_THEME['cohort_mid']],
            [1.0, SURF_THEME['cohort_max']]
        ],
        zmin=0,
        zmax=100,
        showscale=True,
        colorbar=dict(title="Retenção %", len=0.85)
    ))
    
    fig_cohort.update_layout(
        plot_bgcolor=SURF_THEME['pure_white'],
        paper_bgcolor=SURF_THEME['pure_white'],
        margin=dict(l=40, r=20, t=10, b=40),
        font=dict(family="Roboto", color=SURF_THEME['obsidian_black']),
        height=380
    )
    fig_cohort.update_xaxes(side="top", tickfont=dict(size=11, family="Roboto"))
    fig_cohort.update_yaxes(autorange="reversed", tickfont=dict(size=11, family="Roboto"))
    st.plotly_chart(fig_cohort, width="stretch")
else:
    st.info("Nenhum dado de safra para os filtros selecionados.")

with st.expander("🔍 Visualizar e Exportar Dados Consolidados (CSV)"):
    st.dataframe(
        df_monthly.rename(columns={
            "month_start": "Mês de Referência",
            "active_customers": "Clientes Ativos",
            "healthy_customers": "Ativos Saudáveis",
            "grace_customers": "Grace Period",
            "base_customers": "Base do Mês",
            "revenue_lost": "Receita Perdida - Churn (R$)",
            "churn_customers": "Cancelamentos",
            "total_revenue": "Receita Reconhecida (R$)",
            "arpu": "ARPU (R$)",
            "churn_rate": "Churn Rate (%)",
            "revenue_at_risk": "Receita sob Risco (R$)"
        }),
        width="stretch"
    )
    
    csv_data = df_monthly.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Baixar Dados Consolidados (.csv)",
        data=csv_data,
        file_name="sp_telecom_consolidado_crm.csv",
        mime="text/csv"
    )

st.markdown(f"""
    <div style="text-align: center; margin-top: 50px; padding: 22px 16px; color: {SURF_THEME['slate_gray']}; font-size: 0.78rem; border-top: 1px solid {SURF_THEME['card_border']}; background-color: {SURF_THEME['pure_white']}; border-radius: 10px;">
        <p style="margin: 0; font-weight: 600; color: {SURF_THEME['obsidian_black']};">
            ⚠️ Nota de Isenção e Conformidade
        </p>
        <p style="margin: 6px 0 0 0;">
            Todos os dados, nomes, métricas financeiras e indicadores apresentados neste dashboard são <strong>estritamente fictícios</strong>, gerados por modelo sintético para fins demonstrativos, de portfólio e análise de retenção.
        </p>
        <p style="margin: 4px 0 0 0; font-size: 0.72rem; color: #94A3B8;">
            © SP Telecom — Dashboard Analítico de CRM e Retenção
        </p>
    </div>
""", unsafe_allow_html=True)