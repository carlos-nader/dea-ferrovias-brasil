# 00 — Download e preparação do IPCA

Script: `R/00_download_ipca.R`
Outputs: `data/ipca_mensal.csv`, `data/ipca_anual.csv`

---

## Fonte

Banco Central do Brasil — SGS (Sistema Gerenciador de Séries Temporais)
Série **433**: IPCA variação % mensal, divulgada pelo IBGE.
Acesso via pacote R `rbcb` (função `get_series`).

Cobertura: janeiro/2008 a dezembro/2024 (alinhada ao período das Demonstrações Financeiras).

---

## Índice mensal acumulado

Base: **janeiro/2008 = 100**.

A partir das variações mensais, constrói-se um índice de preços contínuo:

```
indice(t) = 100 × ∏(1 + ipca_k/100) / (1 + ipca_jan2008/100)
             para k = jan/2008 até t
```

Salvo em `ipca_mensal.csv` para permitir auditoria do cálculo anual.

---

## Índice médio anual (deflator)

Para deflacionar receita anual (variável de fluxo), o deflator correto é o
**nível médio de preços do ano**, não a variação acumulada de dezembro a dezembro.
A receita anual representa transações distribuídas ao longo dos 12 meses; usar
o índice de dezembro subestimaria a inflação efetiva do período.

```
indice_medio(ano) = média dos 12 valores mensais do índice naquele ano
```

Deflação aplicada no script `01_correlacao_tku_receita.R`:

```r
receita_real = receita_nominal × (indice_medio_2008 / indice_medio_ano)
```

---

## Estrutura dos CSVs

**`ipca_mensal.csv`**

| Coluna           | Tipo    | Descrição                                  |
|------------------|---------|--------------------------------------------|
| `date`           | date    | Primeiro dia do mês de referência          |
| `ipca_mensal_pct`| numeric | Variação % mensal do IPCA                  |
| `indice`         | numeric | Índice acumulado (base jan/2008 = 100)     |

**`ipca_anual.csv`**

| Coluna          | Tipo    | Descrição                                       |
|-----------------|---------|-------------------------------------------------|
| `ano`           | integer | Ano de referência                               |
| `ipca_acum_pct` | numeric | Variação acumulada anual % (dez a dez)          |
| `indice_medio`  | numeric | Média dos índices mensais do ano (base 2008=100)|
