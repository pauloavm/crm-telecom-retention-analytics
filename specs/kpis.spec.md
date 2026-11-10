# Especificação de KPIs e Regras de Negócio (SDD)

> Spec-Driven Development: este documento é a **fonte da verdade** das métricas.
> Cada regra tem um ID (`RN-xx` / `KPI-xx`) e é verificada por pelo menos um teste
> automatizado em `tests/` (o ID aparece no nome ou docstring do teste).
> Mudou a regra? Mude primeiro aqui, depois o teste, por último o código.

## 1. Domínio

| Termo | Definição |
|---|---|
| Mês de referência | `customer_monthly.month_start` (sempre dia 1, formato `YYYY-MM-DD`). |
| Safra (cohort) | `customers.cohort_month` — mês de aquisição do cliente. |
| Tenure | `customer_monthly.tenure_month` — meses desde a safra (M0 = mês de entrada). |

## 2. Regras de negócio (geração de dados)

| ID | Regra |
|---|---|
| RN-01 | Atraso de **1 a 15 dias** ⇒ status `GRACE_PERIOD` (cliente ativo, receita reconhecida, receita **sob risco** = mensalidade). |
| RN-02 | Atraso **> 15 dias** ⇒ status `CHURN` (cliente inativo, receita reconhecida = 0). |
| RN-03 | Sem atraso e sem churn comportamental ⇒ status `ACTIVE` (receita sob risco = 0). |
| RN-04 | `CHURN` é **terminal**: não existe registro mensal do cliente após o mês do churn. |
| RN-05 | `customers.current_status = 'CHURN'` ⇔ existe registro `CHURN` em `customer_monthly`, e `churn_date` = mês desse registro. |
| RN-06 | O histórico mensal de um cliente é **contíguo**: começa na safra (tenure 0) e avança 1 mês por registro. |
| RN-07 | `payments` tem exatamente 1 fatura por (cliente, mês) espelhando `customer_monthly`; `days_overdue` idêntico. |

## 3. KPIs

| ID | KPI | Fórmula (para um mês *m*, sob os filtros aplicados) |
|---|---|---|
| KPI-01 | Clientes ativos | `COUNT(DISTINCT customer_id) WHERE active_flag = 1` (inclui `GRACE_PERIOD`). |
| KPI-02 | Ativos saudáveis | `COUNT(DISTINCT customer_id) WHERE status = 'ACTIVE'`. Saudáveis + Grace = KPI-01 (sem dupla contagem). |
| KPI-03 | Receita reconhecida | `SUM(recognized_revenue)`. |
| KPI-04 | ARPU | KPI-03 / KPI-01 (0 quando não há ativos). |
| KPI-05 | Churn rate (%) | `churns(m) / base_inicial(m) × 100`, onde `base_inicial(m)` = clientes com registro no mês (ativos + churns). Sempre entre 0 e 100. |
| KPI-06 | Receita sob risco | `SUM(revenue_at_risk) WHERE status = 'GRACE_PERIOD'`. Receita de clientes já cancelados **não** é "sob risco" — é receita perdida. |
| KPI-07 | Receita perdida (churn) | `SUM(monthly_fee) WHERE status = 'CHURN'`. |
| KPI-08 | Retenção de safra (%) | `ativos(safra, tenure) / tamanho_total_da_safra × 100`. O denominador é o total de clientes adquiridos na safra (tabela `customers`), **independe** da janela de datas. Sempre entre 0 e 100 e não-crescente ao longo do tenure. |

### Cartões do topo (dashboard)
Os cartões mostram o **último mês da janela selecionada** — nunca o último mês global do banco — e a variação de KPI-01 em relação ao mês anterior da mesma janela.

## 4. Critérios de aceitação da interface (E2E)

| ID | Critério |
|---|---|
| UI-01 | A página carrega sem exceções e exibe o título "Telecom CRM & Retention Dashboard". |
| UI-02 | Exibe 4 cartões de KPI: Clientes Ativos, ARPU, Churn, Receita sob Risco. |
| UI-03 | Exibe 3 gráficos: Faturamento vs ARPU, Composição da Base, Matriz de Cohort. |
| UI-04 | Aplicar um filtro (ex.: Plano) atualiza os KPIs sem erro. |
| UI-05 | O botão de exportação gera um CSV com as colunas do consolidado mensal. |
| UI-06 | Layout utilizável em viewport mobile (390px) sem erro de renderização. |
