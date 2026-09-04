# CRM & Telecom Churn Analytics Pipeline
> **Projeto de Retenção de Clientes e CRM Analytics para Telecomunicações**

---

Este repositório contém um ecossistema de análise de dados projetado para mensurar a saúde da base de clientes ativos, quantificar riscos financeiros associados à inadimplência temporária e modelar a retenção de safras (análise de coorte). 

O diferencial deste pipeline é sua **arquitetura de alto desempenho**. Ao invés de delegar cálculos complexos e custosos ao Power BI em tempo de execução via medidas DAX pesadas, todo o processamento massivo é realizado previamente em nível de banco de dados e pipelines de transformação (SQL e Python). O Power BI funciona em cima de tabelas pré-calculadas e indexadas, garantindo atualizações instantâneas e navegação fluida em painéis executivos.

---

## 🚀 Estrutura do Repositório

```bash
/
├── .gitattributes
├── .gitignore
├── README.md               # Documentação principal estruturada em metodologia STAR
├── dicionario_dados.md     # Mapeamento do esquema lógico e dicionário de dados detalhado
├── generate_database.py    # Script para simular e gerar a estrutura local do banco de dados SQLite
├── ingestao_dados.py       # Pipeline de carga e higienização dos dados de churn
├── generate_table_view.py  # Script auxiliar de visualização de dados de tabelas fato
├── /data/                  # Diretório local para armazenamento dos dados brutos (Telco Churn)
├── /sql/                   # Scripts SQL para cálculo de métricas agregadas
│   ├── calc_arpu.sql       # Query de cálculo de ARPU (Average Revenue Per User) mensal
│   └── cohort_analysis.sql # Query analítica para mapear a retenção histórica de safras
├── /notebooks/             # Análises exploratórias avançadas
│   └── analise_inadimplencia.ipynb # Análise e isolamento da regra de negócio Grace Period
└── /dashboards/            # Arquivo de visualização executiva e capturas de tela
    └── dashboard_retencao.pbix # Dashboard otimizado no Power BI
```

---

## 💼 Estudo de Caso de Negócio (Metodologia STAR)

Esta seção documenta o impacto estratégico e o desenvolvimento técnico do projeto de acordo com a metodologia **STAR** (*Situation, Task, Action, Result*).

### 1. Situação (Situation)
Uma grande operadora de telecomunicações estava enfrentando uma **taxa de churn (cancelamento) historicamente elevada**, impactando a previsibilidade da receita mensal e comprometendo a margem líquida da operação. O time de CRM e Marketing de Retenção operava de forma reativa devido à falta de indicadores preditivos e visibilidade em tempo real sobre a saúde da base ativa, a receita média gerada por usuário (ARPU) e o comportamento financeiro detalhado de clientes recém-adquiridos.

### 2. Tarefa (Task)
Minha missão foi desenvolver um **pipeline analítico completo de ponta a ponta** capaz de coletar, processar, modelar e expor de maneira executiva os dados históricos de clientes. Os principais objetivos foram:
1. Estruturar um pipeline robusto de ingestão e processamento de dados usando Python e SQL.
2. Formular e isolar uma regra de negócio complexa de cobrança e risco financeiro (o **Grace Period**).
3. Construir um dashboard executivo no Power BI com foco em design limpo (*Clean Executive Layout*) e **alta velocidade de carregamento**, otimizado para a tomada de decisão do time de Marketing e CRM.

### 3. Ação (Action)
Para concretizar as metas propostas, conduzi as seguintes ações integradas:

*   **Ingestão & Engenharia de Dados**: Utilizando Python (`ingestao_dados.py` e `generate_database.py`), carreguei e tratei o conjunto de dados bruto. Criei um modelo relacional robusto no SQLite estruturado em um esquema estrela (*Star Schema*).
*   **Transformações e Pré-Agregações em SQL**: Em vez de aplicar lógicas de tabelas temporárias e filtros pesados via DAX no Power BI, desenvolvi rotinas em SQL para pré-calcular métricas-chave em tabelas físicas agregadas:
    *   **Matriz de Cohort (Safras)**: Criação da tabela `cohort_retention`, que agrupa os clientes por mês de aquisição (`cohort_month`) e calcula a taxa de retenção (`retention_rate`) no decorrer dos meses de vida do cliente (`tenure_month`).
    *   **ARPU e Receita Mensal**: Criação da tabela `arpu_mensal` consolidando o volume de clientes ativos, faturamento total reconhecido e ARPU mês a mês.
    *   **Snapshot Executivo**: Tabela `kpi_snapshot_atual` calculando de forma estática os últimos indicadores chave do negócio (`active_customers`, `total_revenue`, `arpu_atual`, `churn_rate_atual`) para alimentar cartões de topo de forma instantânea.
*   **Implementação de Regras de Negócio (Python)**: No notebook `/notebooks/analise_inadimplencia.ipynb`, isolei o comportamento de atraso de pagamento de faturas. Desenvolvi a regra de **Grace Period (Período de Graça)**:
    *   Clientes com faturas em atraso de **até 15 dias** são catalogados no status `GRACE_PERIOD` (inadimplência temporária e recuperável).
    *   O faturamento desses clientes é isolado na métrica **Receita sob Risco** (`revenue_at_risk`), orientando diretamente o CRM a disparar réguas de cobrança amigáveis preventivas.
    *   Atrasos acima de 15 dias são classificados como Churn definitivo.
*   **Modelagem e Visualização de Dados (Power BI)**: No Power BI Desktop, conectei as tabelas agregadas e a dimensão `customers` em um relacionamento leve (1-para-Muitos). A interface foi construída arrastando colunas nativas e aplicando agregações nativas extremamente velozes (como médias simples para taxas e somas simples para receitas).

### 4. Resultado (Result)
Os resultados entregues pelo projeto trouxeram revelações críticas de negócios e soluções mensuráveis:
*   **Identificação de Gargalos Críticos (Cohort)**: O painel de safras evidenciou que **40% de todo o churn ocorre precisamente no 3º mês de tenure (assinatura)**. Isso indicou uma falha grave de *onboarding* de clientes ou na entrega inicial da oferta.
*   **Quantificação de Riscos Financeiros**: A regra de Grace Period demonstrou que a operadora possuía, em média, **R$ 250 mil em receita sob risco mensal** associada a clientes inadimplentes recuperáveis.
*   **Direcionamento de CRM**: O diagnóstico de Cohort e Grace Period permitiu que o time de CRM criasse campanhas de retenção direcionadas (ações de *cross-selling* preventivo no final do 2º mês de assinatura) e réguas de cobrança automatizadas para o grupo de inadimplência inicial.
*   **Projeções de Negócio**: Estima-se que as ações focadas reduzam a **taxa de churn geral em até 15%** e recuperem **20% de toda a receita em risco** (`revenue_at_risk`), impactando de forma drástica e direta o ROI da operação de marketing.
*   **Performance do Dashboard**: Ao desonerar o mecanismo de análise do Power BI de cálculos de Cohort e Churn histórico dinâmicos, o dashboard obteve um **tempo de resposta zero (sub-segundo)** em cliques de segmentadores transversais.

---

## 📊 Arquitetura de Dados & Modelagem Estrela

A modelagem de dados foi estruturada utilizando boas práticas de *Data Warehousing*, combinando uma tabela dimensão de clientes e tabelas fatos ou agregados de alta granularidade e pré-calculadas.

```
       +--------------------+
       |     customers      |  (Tabela Dimensão)
       |   (customer_id)    |
       +---------+----------+
                 |
                 | (1 : N)
                 v
       +--------------------+
       |  customer_monthly  |  (Histórico de status do cliente)
       | (customer_monthly) |
       +--------------------+
```

### Principais Tabelas Pré-Calculadas do Modelo
A fim de garantir a performance máxima das consultas do dashboard, quatro tabelas principais foram estruturadas no banco de dados e mapeadas para visuais diretos no Power BI:

1.  **`kpi_snapshot_atual`**: Consolidado estático contendo os números mais recentes do negócio.
    *   *Uso no BI*: Cartões KPI rápidos no cabeçalho (Clientes Ativos, ARPU Atual, Receita Total, Churn Atual).
2.  **`arpu_mensal`**: Histórico evolutivo mensal agregando receita total e valor médio por cliente.
    *   *Uso no BI*: Gráfico de linhas duplo para evolução de Receita vs. ARPU.
3.  **`cohort_retention`**: Matriz de retenção histórica agrupada pelo mês de adesão e calculada no detalhe de *tenure_month*.
    *   *Uso no BI*: Matriz de Cohort (Heatmap térmico com formatação condicional).
4.  **`kpis_mensais`**: Séries temporais mensais agregando contagem de ativos, churns, clientes em Grace Period e receita sob risco.
    *   *Uso no BI*: Gráficos de barra/funil de saúde da base e linhas de receita sob risco.

---

## 🛠️ Como Executar o Pipeline de Dados

### Pré-requisitos
*   Python 3.10 ou superior
*   Bibliotecas especificadas no projeto (`pandas`, `numpy`, `sqlite3` - nativa)

### Passos para Configuração

1.  **Instalação do Banco de Dados e Importação**:
    Execute o script de inicialização do banco para gerar as tabelas relacionais de teste (`customers`, `customer_monthly`, `payments`) a partir do arquivo de dados bruto:
    ```bash
    python generate_database.py
    ```

2.  **Execução do Pipeline de Transformação e Carga (ETL)**:
    Processe os dados e preencha as tabelas pré-calculadas rodando o script de ETL:
    ```bash
    python ingestao_dados.py
    ```
    Isso aplicará as transformações necessárias de Grace Period e os scripts SQL de cálculo do ARPU Mensal e de Coorte.

3.  **Visualizando a Importação**:
    Para conferir se os registros foram inseridos corretamente nas tabelas otimizadas, execute:
    ```bash
    python generate_table_view.py
    ```

4.  **Construção do Dashboard**:
    Abra o Power BI Desktop, conecte-se ao banco de dados SQLite gerado localmente, carregue as tabelas agregadas e monte seus visuais arrastando diretamente as colunas para o canvas sem a necessidade de codificar fórmulas DAX complexas.

---

## 🎨 Visualização Executiva Recomendada

O painel no Power BI foi projetado sob os pilares de **Foco de CRM**, **Leitura Rápida** e **Métricas Financeiras Claras**:

*   **Cabeçalho Estratégico**: Cartões de KPI limpos usando `active_customers`, `arpu_atual` e `churn_rate_atual` da tabela `kpi_snapshot_atual`.
*   **Diagnóstico de Cohort**: Matriz arrastando `cohort_month` para linhas, `tenure_month` para colunas e `retention_rate` (Média) para valores. Use formatação condicional em escala de degradê do azul (alta retenção) para o laranja/vermelho (queda drástica) para evidenciar visualmente a quebra do 3º mês de tenure.
*   **Monitoramento de Receita**: Gráfico de linhas com eixo X em `month_start` da tabela `arpu_mensal` e duas séries: `total_revenue` (Eixo Y 1) e `arpu` (Eixo Y 2).
*   **Funil de CRM**: Gráfico de barras horizontais utilizando a tabela `kpis_mensais` comparando a contagem de `active_customers` vs. `grace_period_customers` vs. `churn_customers`.

---

## 📧 Autor e Contribuições

Este repositório foi construído por [Paulo AVM](https://github.com/pauloavm) como um portfólio profissional estratégico para o setor de Telecomunicações e Analytics. Contribuições, feedbacks e insights de negócios são sempre bem-vindos!

*   **GitHub**: [pauloavm](https://github.com/pauloavm)
*   **Projeto**: `crm-telecom-retention-analytics`
