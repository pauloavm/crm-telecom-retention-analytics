import os
import sqlite3
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Surf Telecom — CRM & Retention Analytics",
    page_icon="📶",
    layout="wide",
    initial_sidebar_state="expanded"
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
    """Detects database file in current path or parent directory, or creates synthetic fallback."""
    possible_paths = [
        "telecom_crm_.sqlite",
        "telecom_crm.sqlite",
        "data/telecom_crm_.sqlite",
        "data/telecom_crm.sqlite",
        "../telecom_crm_.sqlite"
    ]
    db_file = None
    for p in possible_paths:
        if os.path.exists(p):
            db_file = p
            break
            
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
        
        is_active = True
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
                SURF <span style="color: {SURF_THEME['obsidian_black']};">TELECOM</span>
            </div>
            <div style="font-size: 0.72rem; color: {SURF_THEME['slate_gray']}; font-weight: 500;">
                BOSSS PLATFORM — INTELLIGENCE
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
            <div style="font-size: 0.75rem; font-weight: 700; color: {SURF_THEME['cobalt_blue']};">BRAND IDENTITY VERIFIED</div>
            <div style="font-size: 0.7rem; color: {SURF_THEME['slate_gray']}; margin-top: 4px;">
                Palette: Cobalt Blue (#0012FF), Obsidian Black (#111111), Chalk White (#F3F3F3).
            </div>
        </div>
    """, unsafe_allow_html=True)

where_clauses = ["1=1"]
params = []

if selected_plans:
    where_clauses.append(f"c.plan IN ({','.join(['?']*len(selected_plans))})")
    params.extend(selected_plans)
if selected_contracts:
    where_clauses.append(f"c.contract_type IN ({','.join(['?']*len(selected_contracts))})")
    params.extend(selected_contracts)
if selected_states:
    where_clauses.append(f"c.state IN ({','.join(['?']*len(selected_states))})")
    params.extend(selected_states)
if month_range[0] and month_range[1]:
    where_clauses.append("cm.month_start BETWEEN ? AND ?")
    params.extend([month_range[0], month_range[1]])

where_sql = " AND ".join(where_clauses)

@st.cache_data(ttl=300)
def query_dashboard_data(where_stmt, query_params):
    sql_monthly = f"""
        SELECT 
            cm.month_start,
            COUNT(DISTINCT CASE WHEN cm.active_flag = 1 THEN cm.customer_id END) AS active_customers,
            COUNT(DISTINCT CASE WHEN cm.revenue_at_risk > 0 AND cm.active_flag = 1 THEN cm.customer_id END) AS grace_customers,
            COUNT(DISTINCT CASE WHEN cm.churn_flag = 1 THEN cm.customer_id END) AS churn_customers,
            COALESCE(SUM(cm.recognized_revenue), 0.0) AS total_revenue,
            COALESCE(SUM(CASE WHEN cm.month_start = (SELECT MAX(month_start) FROM customer_monthly) THEN cm.revenue_at_risk ELSE 0 END), 0.0) AS revenue_at_risk
        FROM customer_monthly cm
        JOIN customers c ON c.customer_id = cm.customer_id
        WHERE {where_stmt}
        GROUP BY cm.month_start
        ORDER BY cm.month_start ASC;
    """
    df_monthly = pd.read_sql_query(sql_monthly, conn, params=query_params)
    
    # Calculate ARPU and Churn % dynamically
    df_monthly['arpu'] = np.where(df_monthly['active_customers'] > 0, df_monthly['total_revenue'] / df_monthly['active_customers'], 0.0)
    df_monthly['churn_rate'] = np.where(df_monthly['active_customers'] > 0, (df_monthly['churn_customers'] / df_monthly['active_customers']) * 100, 0.0)
    
    # Cohort query
    sql_cohort = f"""
        SELECT 
            c.cohort_month,
            cm.tenure_month,
            COUNT(DISTINCT CASE WHEN cm.active_flag = 1 THEN cm.customer_id END) AS active_in_tenure
        FROM customer_monthly cm
        JOIN customers c ON c.customer_id = cm.customer_id
        WHERE {where_stmt}
        GROUP BY c.cohort_month, cm.tenure_month
        ORDER BY c.cohort_month ASC, cm.tenure_month ASC;
    """
    df_cohort = pd.read_sql_query(sql_cohort, conn, params=query_params)
    
    return df_monthly, df_cohort

df_monthly, df_cohort_raw = query_dashboard_data(where_sql, params)

st.markdown(f"""
    <div class="main-header">
        <div>
            <div class="brand-badge">Operadora Móvel 100% Nacional</div>
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

if not df_monthly.empty:
    last_row = df_monthly.iloc[-1]
    prev_row = df_monthly.iloc[-2] if len(df_monthly) > 1 else last_row
    
    cur_active = int(last_row['active_customers'])
    prev_active = int(prev_row['active_customers'])
    active_diff_pct = ((cur_active - prev_active) / prev_active * 100) if prev_active > 0 else 0.0
    
    cur_arpu = float(last_row['arpu'])
    cur_churn = float(last_row['churn_rate'])
    cur_risk = float(last_row['revenue_at_risk'])
else:
    cur_active, active_diff_pct, cur_arpu, cur_churn, cur_risk = 0, 0.0, 0.0, 0.0, 0.0

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
            <div class="metric-sub">Receita média por usuário ativo</div>
        </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Taxa de Churn Atual</div>
            <div class="metric-value" style="color: {'#EF4444' if cur_churn > 8 else '#111111'};">{cur_churn:.2f}%</div>
            <div class="metric-sub">Cancelados / Total Ativos</div>
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
    st.markdown(f"#### 📈 Evolução Financeira: Faturamento vs. ARPU")
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
        st.plotly_chart(fig_fin, use_container_width=True)
    else:
        st.info("Nenhum dado encontrado para os filtros selecionados.")

with col_right:
    st.markdown(f"#### 👥 Composição da Base de Clientes")
    if not df_monthly.empty:
        fig_comp = go.Figure()
        
        fig_comp.add_trace(go.Bar(
            x=df_monthly['month_start'],
            y=df_monthly['active_customers'],
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
        st.plotly_chart(fig_comp, use_container_width=True)
    else:
        st.info("Nenhum dado disponível.")

st.markdown("#### 🧊 Matriz Térmica de Cohort (Retenção por Safra)")
st.markdown(
    "<span style='color: #64748B; font-size: 0.82rem;'>Percentual de clientes mantidos ativos em relação ao Tenure 0 (Entrada na base).</span>",
    unsafe_allow_html=True
)

if not df_cohort_raw.empty:
    # Pivot raw counts
    pivot_counts = df_cohort_raw.pivot(index='cohort_month', columns='tenure_month', values='active_in_tenure')
    
    # Calculate initial cohort size (Tenure 0 or first available column)
    if 0 in pivot_counts.columns:
        cohort_sizes = pivot_counts[0]
    else:
        cohort_sizes = pivot_counts.bfill(axis=1).iloc[:, 0]
        
    # Retention matrix calculation
    cohort_retention = pivot_counts.divide(cohort_sizes, axis=0) * 100.0
    
    # Restrict tenure columns to reasonable display window (up to 12 or 15)
    max_cols = min(13, len(cohort_retention.columns))
    cohort_display = cohort_retention.iloc[:, :max_cols].round(1)
    
    # Format labels
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
        zmin=20,
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
    st.plotly_chart(fig_cohort, use_container_width=True)
else:
    st.info("Nenhum dado de safra para os filtros selecionados.")

with st.expander("🔍 Visualizar e Exportar Dados Consolidados (CSV)"):
    st.dataframe(
        df_monthly.rename(columns={
            "month_start": "Mês de Referência",
            "active_customers": "Clientes Ativos",
            "grace_customers": "Grace Period",
            "churn_customers": "Cancelamentos",
            "total_revenue": "Receita Reconhecida (R$)",
            "arpu": "ARPU (R$)",
            "churn_rate": "Churn Rate (%)",
            "revenue_at_risk": "Receita sob Risco (R$)"
        }),
        use_container_width=True
    )
    
    csv_data = df_monthly.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Baixar Dados Consolidados (.csv)",
        data=csv_data,
        file_name="surf_telecom_consolidado_crm.csv",
        mime="text/csv"
    )