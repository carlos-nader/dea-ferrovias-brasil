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

## Abordagem alternativa — Ipeadata (Excel)

O mesmo deflator pode ser obtido diretamente do Ipeadata sem código:

1. Acessar [ipeadata.gov.br](https://www.ipeadata.gov.br) → série **PRECOS12_IPCA12**
   (*Índice nacional de preços ao consumidor amplo — geral: índice dez/1993 = 100*)
2. Baixar a série em Excel (`deflator_ipca.xls`, arquivo em `data/`)
3. Calcular o deflator com uma fórmula simples:

```text
deflator(t) = IPCA_ibge(t) / IPCA_ibge(jan/2012)
```

O resultado é numericamente equivalente ao `indice/100` do CSV
(diferença máxima verificada: 0,000012 — apenas arredondamento de ponto flutuante).

Esta abordagem é mais direta quando não se dispõe de acesso à API do BCB ou
quando se prefere rastrear a fonte primária no próprio arquivo de dados.

---

## Estrutura do CSV

**`ipca_mensal.csv`**

| Coluna            | Tipo     | Descrição                              |
|-------------------|----------|----------------------------------------|
| `date`            | data     | Primeiro dia do mês de referência      |
| `ipca_mensal_pct` | numérico | Variação % mensal do IPCA              |
| `indice`          | numérico | Índice acumulado (base jan/2012 = 100) |
