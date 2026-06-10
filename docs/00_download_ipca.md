# 00 — Download e preparação do IPCA

Script: `R/00_download_ipca.R`
Outputs: `data/ipca_mensal.csv`, `data/ipca_anual.csv`

---

## Fonte

Banco Central do Brasil — SGS (Sistema Gerenciador de Séries Temporais)
Série **433**: IPCA variação % mensal, divulgada pelo IBGE.
Acesso via pacote R `rbcb` (função `get_series`).

Cobertura: janeiro/2012 a dezembro/2025 (alinhada ao período dos dados SIREF).

---

## Índice mensal acumulado

Base: **janeiro/2012 = 100**.

Janeiro/2012 é o primeiro mês da série de receita de frete (SIREF) e o ponto de
partida da análise. A partir das variações mensais, constrói-se um índice contínuo
por composição:

```text
indice(jan/2012) = 100
indice(t)        = indice(t-1) × (1 + ipca(t) / 100)
```

Para deflacionar a receita nominal do mês t a preços de jan/2012:

```r
receita_real(t) = receita_nominal(t) / (indice(t) / 100)
```

Salvo em `ipca_mensal.csv`.

---

## Estrutura do CSV

**`ipca_mensal.csv`**

| Coluna            | Tipo     | Descrição                              |
|-------------------|----------|----------------------------------------|
| `date`            | data     | Primeiro dia do mês de referência      |
| `ipca_mensal_pct` | numérico | Variação % mensal do IPCA              |
| `indice`          | numérico | Índice acumulado (base jan/2012 = 100) |
