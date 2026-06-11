# 02 — Correlação TKU × Receita

Script: `R/02_correlacao_tku_receita.R`
Output: `output/02_correlacao_tku_receita/`

---

## Objetivo

Testar se TKU (Tonelada-Quilômetro Útil) e receita de frete são variáveis
redundantes para fins de DEA. Critério: se r > 0,90 (Pearson), a receita é
descartada e o período de análise permanece 2006–2025 (apenas TKU). Se r ≤ 0,90,
a receita adiciona informação e deve ser considerada como variável de output,
restringindo o período a 2012–2025 (disponibilidade do SIREF).

Teste realizado para todas as 12 DMUs candidatas, individualmente e em painel
poolado.

---

## Método

### Correlação de Pearson — e não regressão

A relação entre TKU e receita é **simétrica**: nenhuma das variáveis é dependente
da outra no sentido causal. O objetivo é verificar se as duas medem a mesma
dimensão do desempenho (redundância), não estimar um efeito ou fazer previsão.
A regressão impõe uma assimetria (variável dependente × independente) que não
existe aqui. O coeficiente de Pearson r mede a associação linear sem pressupor
direcionalidade, sendo o instrumento correto para o teste de redundância.

### Limiar r > 0,90

Critério usual na literatura de DEA para identificar outputs redundantes: se
r > 0,90, as duas variáveis capturam essencialmente a mesma informação e incluir
ambas no modelo não acrescenta poder discriminatório — podendo até distorcer os
scores por colinearidade. Abaixo desse limiar, as variáveis medem dimensões
distintas do desempenho e a inclusão de ambas é metodologicamente justificada.

---

## Dados utilizados

### TKU

- Fonte: Anuário Estatístico ANTT, aba `2.1.2`
- Arquivos: `data/<DMU>/<dmu>_tku_mensal.csv` (gerados por `R/01_extrair_tku_mensal.R`)
- Período: janeiro/2012 a dezembro/2025 (168 meses por DMU)
- Unidade: TKU (valor absoluto)

### Receita de frete

- Fonte: SIREF (Sistema de Informações Regulatórias Ferroviárias — ANTT)
- Contas: **3.1.1** (Receita dos Serviços de Transporte de Carga) +
  **3.1.7** (Receita de Venda de Capacidade Instalada — OFIs), quando presentes
- Arquivos: `data/<DMU>/<dmu>_receita_siref.csv`
- Período: janeiro/2012 a dezembro/2025 (168 meses por DMU)
- Unidade: R$ correntes

A composição 3.1.1 + 3.1.7 captura toda a receita efetiva de transporte de
carga, independente do modelo operacional (operação direta ou concessão de
capacidade a OFIs), excluindo tráfego mútuo (3.1.3), direito de passagem (3.1.4)
e receitas acessórias (3.1.5).

**Nota sobre a FTL:** a série de receita combina TLSA (jan/2012 a dez/2012 e
parte de 2013) + FTL (2013–2025), refletindo a cisão da CFN em 2013. A série
TKU do Anuário trata a concessão como unidade contínua sob a sigla FTL.

### Deflator

- Fonte: BCB SGS série 433 (IPCA variação % mensal, IBGE)
- Arquivo: `data/ipca_mensal.csv` (gerado por `R/00_download_ipca.R`)
- Base: **janeiro/2012 = 100**
- Metodologia: ver `docs/00_download_ipca.md`

---

## Deflação

A receita nominal de cada mês t é convertida a preços de janeiro/2012:

```text
receita_real(t) = receita_nominal(t) / (indice(t) / 100)
```

---

## Resultados

Período: janeiro/2012 a dezembro/2025 — 168 observações mensais por DMU.

| Estatística    | Valor  |
|----------------|-------:|
| r poolado      | 0,9074 |
| n (observações)| 2.016  |

O r poolado (0,91) supera o limiar de 0,90. Apesar de refletir principalmente a
diferença de escala entre DMUs grandes e pequenas — não uma correlação mensal
forte dentro de cada concessionária, houve uma dispersão entre as concessionárias. Ou seja, há concessionárias com coeficiente de correlação baixo e outras com coeficiente de correlação acima de 0,9.

### Avaliação da receita como output

Modelar DMUs
com uma variável de receita que se comporta de forma distinta
entre elas comprometeria a comparabilidade dos scores DEA.

**Conclusão provável:** a receita de frete não será utilizada como output.
O modelo DEA usará apenas TKU, cobrindo o período 2006–2025 com 11 DMUs
(excluindo FNS, sem dados de TKU anteriores a 2012). Decisão a confirmar
com a orientadora e com o Prof. Gildemir.

---

## Próximo passo

Confirmar com a orientadora (Profa. Maisa) e com o Prof. Gildemir a exclusão
da receita como output, com base na dispersão dos r individuais e na
inconsistência da variável entre concessionárias. Aprovada a exclusão,
a especificação do modelo DEA fica definida:

- **Output:** TKU (único)
- **Período:** 2006–2025
- **DMUs:** 11 (EFC, EFVM, FERROESTE, FCA, FTC, FTL, MRS, RMN, RMO, RMP, RMS)

Essa definição desbloqueia a redação do projeto de pesquisa (prazo: 31/07/2026).
