# Dicionario de Dados

## Tabela: arpu_mensal

| Coluna | Tipo | Nulo | Chave Primaria | Comentario |
|---|---|---|---|---|
| month_start | DATE | False | False |  |
| active_customers | BIGINT | False | False |  |
| total_revenue | DECIMAL(32, 2) | True | False |  |
| arpu | DECIMAL(33, 2) | True | False |  |

### Amostra de dados (10 primeiras linhas)

| month_start | active_customers | total_revenue | arpu |
|---|---|---|---|
| 2024-01-01 | 40534 | 4045096.6 | 99.8 |
| 2024-02-01 | 74001 | 7375449.9 | 99.67 |
| 2024-03-01 | 102521 | 10235717.9 | 99.84 |
| 2024-04-01 | 126688 | 12650801.2 | 99.86 |
| 2024-05-01 | 149915 | 14973258.5 | 99.88 |
| 2024-06-01 | 170264 | 17000493.6 | 99.85 |
| 2024-07-01 | 190531 | 19029426.9 | 99.88 |
| 2024-08-01 | 209951 | 20974264.9 | 99.9 |
| 2024-09-01 | 226097 | 22599790.3 | 99.96 |
| 2024-10-01 | 242788 | 24256381.2 | 99.91 |

## Tabela: cohort_retention

| Coluna | Tipo | Nulo | Chave Primaria | Comentario |
|---|---|---|---|---|
| cohort_month | DATE | False | False |  |
| tenure_month | INTEGER | False | False |  |
| cohort_customers | BIGINT | False | False |  |
| active_customers | BIGINT | False | False |  |
| retention_rate | DECIMAL(26, 2) | True | False |  |

### Amostra de dados (10 primeiras linhas)

| cohort_month | tenure_month | cohort_customers | active_customers | retention_rate |
|---|---|---|---|---|
| 2024-01-01 | 0 | 43264 | 40534 | 93.69 |
| 2024-01-01 | 1 | 43264 | 36320 | 83.95 |
| 2024-01-01 | 2 | 43264 | 28556 | 66.0 |
| 2024-01-01 | 3 | 43264 | 25455 | 58.84 |
| 2024-01-01 | 4 | 43264 | 22694 | 52.45 |
| 2024-01-01 | 5 | 43264 | 21255 | 49.13 |
| 2024-01-01 | 6 | 43264 | 19945 | 46.1 |
| 2024-01-01 | 7 | 43264 | 18680 | 43.18 |
| 2024-01-01 | 8 | 43264 | 17496 | 40.44 |
| 2024-01-01 | 9 | 43264 | 16375 | 37.85 |

## Tabela: customer_monthly

| Coluna | Tipo | Nulo | Chave Primaria | Comentario |
|---|---|---|---|---|
| monthly_id | INTEGER | False | True |  |
| customer_id | VARCHAR(36) | False | False |  |
| month_start | DATE | False | False |  |
| tenure_month | INTEGER | False | False |  |
| active_flag | TINYINT | False | False |  |
| churn_flag | TINYINT | False | False |  |
| status | VARCHAR(20) | False | False |  |
| monthly_fee | DECIMAL(10, 2) | False | False |  |
| recognized_revenue | DECIMAL(10, 2) | False | False |  |
| revenue_at_risk | DECIMAL(10, 2) | False | False |  |
| days_overdue | INTEGER | False | False |  |

Chaves estrangeiras:
- ['customer_id'] -> customers.['customer_id']

### Amostra de dados (10 primeiras linhas)

| monthly_id | customer_id | month_start | tenure_month | active_flag | churn_flag | status | monthly_fee | recognized_revenue | revenue_at_risk | days_overdue |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | b62dd314-fd24-46f1-98db-db91344355b7 | 2024-07-01 | 0 | 1 | 0 | ACTIVE | 49.9 | 49.9 | 0.0 | 0 |
| 2 | b62dd314-fd24-46f1-98db-db91344355b7 | 2024-08-01 | 1 | 1 | 0 | ACTIVE | 49.9 | 49.9 | 0.0 | 0 |
| 3 | b62dd314-fd24-46f1-98db-db91344355b7 | 2024-09-01 | 2 | 0 | 1 | CHURN | 49.9 | 0.0 | 49.9 | 0 |
| 4 | 3cbda3c4-5b3f-4e59-a31a-f824817b3324 | 2025-07-01 | 0 | 1 | 0 | ACTIVE | 69.9 | 69.9 | 0.0 | 0 |
| 5 | 3cbda3c4-5b3f-4e59-a31a-f824817b3324 | 2025-08-01 | 1 | 1 | 0 | ACTIVE | 69.9 | 69.9 | 0.0 | 0 |
| 6 | 3cbda3c4-5b3f-4e59-a31a-f824817b3324 | 2025-09-01 | 2 | 0 | 1 | CHURN | 69.9 | 0.0 | 69.9 | 0 |
| 7 | 7942e244-c632-434e-a4f4-d82e8c242a85 | 2024-10-01 | 0 | 1 | 0 | ACTIVE | 89.9 | 89.9 | 0.0 | 0 |
| 8 | 7942e244-c632-434e-a4f4-d82e8c242a85 | 2024-11-01 | 1 | 1 | 0 | GRACE_PERIOD | 89.9 | 89.9 | 89.9 | 2 |
| 9 | 7942e244-c632-434e-a4f4-d82e8c242a85 | 2024-12-01 | 2 | 1 | 0 | ACTIVE | 89.9 | 89.9 | 0.0 | 0 |
| 10 | 7942e244-c632-434e-a4f4-d82e8c242a85 | 2025-01-01 | 3 | 1 | 0 | ACTIVE | 89.9 | 89.9 | 0.0 | 0 |

## Tabela: customers

| Coluna | Tipo | Nulo | Chave Primaria | Comentario |
|---|---|---|---|---|
| customer_id | VARCHAR(36) | False | True |  |
| full_name | VARCHAR(255) | False | False |  |
| email | VARCHAR(255) | False | False |  |
| phone | VARCHAR(50) | True | False |  |
| city | VARCHAR(100) | True | False |  |
| state | VARCHAR(10) | True | False |  |
| gender | VARCHAR(10) | True | False |  |
| birth_date | DATE | True | False |  |
| acquisition_date | DATE | False | False |  |
| cohort_month | DATE | False | False |  |
| plan | VARCHAR(50) | False | False |  |
| contract_type | VARCHAR(50) | False | False |  |
| monthly_fee | DECIMAL(10, 2) | False | False |  |
| current_status | VARCHAR(20) | False | False |  |
| churn_date | DATE | True | False |  |

### Amostra de dados (10 primeiras linhas)

| customer_id | full_name | email | phone | city | state | gender | birth_date | acquisition_date | cohort_month | plan | contract_type | monthly_fee | current_status | churn_date |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0000524c-6ad4-431b-9d8c-3fd3453eb572 | Melissa Melo | melissamelo3@live.com | 87 5843-5954 | Andrade Grande | GO | Outro | 2005-01-05 | 2024-04-11 | 2024-04-01 | Controle 10GB | One year | 49.9 | CHURN | 2024-05-01 |
| 0000651b-1ee4-4144-9683-2f155fe5b6f5 | Gustavo Henrique Souza | gustavohenriquesouza1@hotmail.com | +55 94 4699-8419 | Rodrigues da Praia | SC | F | 1997-10-05 | 2024-01-05 | 2024-01-01 | Controle 10GB | Monthly | 49.9 | CHURN | 2025-12-01 |
| 00008b6a-ad3c-4d93-b536-a6509e778187 | Asafe Sampaio | asafesampaio@hotmail.com | 94 0442-6861 | Castro | RN | F | 1966-09-14 | 2024-08-04 | 2024-08-01 | Controle 20GB | Monthly | 69.9 | CHURN | 2024-09-01 |
| 0000a45d-efb1-4bea-b272-059cc4c6aab9 | Lucca Brito | luccabrito3@yahoo.com.br | +55 82 0207-5785 | Alves do Campo | SC | Outro | 2006-08-13 | 2024-12-19 | 2024-12-01 | Controle 10GB | One year | 49.9 | CHURN | 2025-11-01 |
| 0000bbe7-75ff-4c9a-b611-c2c4b567afe2 | Antony Cavalcante | antonycavalcante1@live.com | +55 53 4620-0212 | Peixoto | AP | Outro | 1961-03-22 | 2025-01-27 | 2025-01-01 | Pós-pago 100GB | One year | 169.9 | CHURN | 2025-02-01 |
| 0000c7e8-53ac-4563-ad53-e31edb15e9b8 | Luana Sampaio | luanasampaio1@icloud.com | 94 7279-6025 | Aragão Grande | MS | Outro | 1985-12-14 | 2025-10-17 | 2025-10-01 | Controle 20GB | Two year | 69.9 | ACTIVE | None |
| 0000dc8e-4fd7-4a16-8679-4aaffca6b3c0 | Benjamim da Conceição | benjamimdaconceicao2@live.com | 47 0789-5479 | Fernandes | SC | F | 1976-03-16 | 2025-05-12 | 2025-05-01 | Controle 20GB | Two year | 69.9 | ACTIVE | None |
| 00012c61-43e0-48d6-85a0-bdb4532cdfe4 | Thales Castro | thalescastro2@uol.com.br | +55 89 8173-8426 | Ferreira | MS | F | 1953-06-16 | 2025-02-01 | 2025-02-01 | Pós-pago 30GB | One year | 89.9 | CHURN | 2025-04-01 |
| 00013142-977d-4ccf-91a9-9c8cc4fbaf04 | Srta. Ana Laura Rodrigues | srtaanalaurarodrigues@outlook.com.br | 42 2909-0610 | Santos | AC | Outro | 1964-08-09 | 2024-11-26 | 2024-11-01 | Pós-pago 30GB | One year | 89.9 | CHURN | 2025-07-01 |
| 000132bd-a12d-433f-b966-714d7ebc5ed3 | Valentina Brito | valentinabrito4@terra.com.br | +55 43 8661-6955 | Macedo | SE | Outro | 1993-04-24 | 2024-11-02 | 2024-11-01 | Controle 10GB | One year | 49.9 | ACTIVE | None |

## Tabela: kpi_snapshot_atual

| Coluna | Tipo | Nulo | Chave Primaria | Comentario |
|---|---|---|---|---|
| month_start | DATE | False | False |  |
| active_customers | BIGINT | False | False |  |
| total_revenue | DECIMAL(32, 2) | True | False |  |
| arpu_atual | DECIMAL(33, 2) | True | False |  |
| churn_rate_atual | DECIMAL(26, 2) | True | False |  |

### Amostra de dados (10 primeiras linhas)

| month_start | active_customers | total_revenue | arpu_atual | churn_rate_atual |
|---|---|---|---|---|
| 2025-12-01 | 309964 | 30958713.6 | 99.88 | 8.72 |

## Tabela: kpis_mensais

| Coluna | Tipo | Nulo | Chave Primaria | Comentario |
|---|---|---|---|---|
| month_start | DATE | False | False |  |
| active_customers | BIGINT | False | False |  |
| grace_period_customers | BIGINT | False | False |  |
| churn_customers | BIGINT | False | False |  |
| revenue_at_risk | DECIMAL(32, 2) | True | False |  |
| churn_rate | DECIMAL(26, 2) | True | False |  |

### Amostra de dados (10 primeiras linhas)

| month_start | active_customers | grace_period_customers | churn_customers | revenue_at_risk | churn_rate |
|---|---|---|---|---|---|
| 2024-01-01 | 34221 | 6313 | 2730 | 906555.7 | 6.31 |
| 2024-02-01 | 62551 | 11450 | 6766 | 1823358.4 | 8.38 |
| 2024-03-01 | 86601 | 15920 | 14587 | 3056929.3 | 12.46 |
| 2024-04-01 | 106818 | 19870 | 17257 | 3697937.3 | 11.99 |
| 2024-05-01 | 126352 | 23563 | 19959 | 4338247.8 | 11.75 |
| 2024-06-01 | 143439 | 26825 | 21525 | 4833775.0 | 11.22 |
| 2024-07-01 | 160815 | 29716 | 22973 | 5261251.1 | 10.76 |
| 2024-08-01 | 177150 | 32801 | 24072 | 5668602.7 | 10.29 |
| 2024-09-01 | 190806 | 35291 | 25511 | 6068959.8 | 10.14 |
| 2024-10-01 | 204746 | 38042 | 26375 | 6426468.3 | 9.8 |

## Tabela: payments

| Coluna | Tipo | Nulo | Chave Primaria | Comentario |
|---|---|---|---|---|
| payment_id | INTEGER | False | True |  |
| customer_id | VARCHAR(36) | False | False |  |
| reference_month | DATE | False | False |  |
| due_date | DATE | False | False |  |
| payment_date | DATE | True | False |  |
| days_overdue | INTEGER | False | False |  |
| payment_status | VARCHAR(20) | False | False |  |
| amount | DECIMAL(10, 2) | False | False |  |

Chaves estrangeiras:
- ['customer_id'] -> customers.['customer_id']

### Amostra de dados (10 primeiras linhas)

| payment_id | customer_id | reference_month | due_date | payment_date | days_overdue | payment_status | amount |
|---|---|---|---|---|---|---|---|
| 1 | b62dd314-fd24-46f1-98db-db91344355b7 | 2024-07-01 | 2024-07-11 | 2024-07-03 | 0 | PAID | 49.9 |
| 2 | b62dd314-fd24-46f1-98db-db91344355b7 | 2024-08-01 | 2024-08-11 | 2024-08-03 | 0 | PAID | 49.9 |
| 3 | b62dd314-fd24-46f1-98db-db91344355b7 | 2024-09-01 | 2024-09-11 | 2024-09-03 | 0 | PAID | 49.9 |
| 4 | 3cbda3c4-5b3f-4e59-a31a-f824817b3324 | 2025-07-01 | 2025-07-11 | 2025-07-08 | 0 | PAID | 69.9 |
| 5 | 3cbda3c4-5b3f-4e59-a31a-f824817b3324 | 2025-08-01 | 2025-08-11 | 2025-08-02 | 0 | PAID | 69.9 |
| 6 | 3cbda3c4-5b3f-4e59-a31a-f824817b3324 | 2025-09-01 | 2025-09-11 | 2025-09-08 | 0 | PAID | 69.9 |
| 7 | 7942e244-c632-434e-a4f4-d82e8c242a85 | 2024-10-01 | 2024-10-11 | 2024-10-03 | 0 | PAID | 89.9 |
| 8 | 7942e244-c632-434e-a4f4-d82e8c242a85 | 2024-11-01 | 2024-11-11 | 2024-11-03 | 2 | GRACE_PERIOD | 89.9 |
| 9 | 7942e244-c632-434e-a4f4-d82e8c242a85 | 2024-12-01 | 2024-12-11 | 2024-12-02 | 0 | PAID | 89.9 |
| 10 | 7942e244-c632-434e-a4f4-d82e8c242a85 | 2025-01-01 | 2025-01-11 | 2025-01-08 | 0 | PAID | 89.9 |
