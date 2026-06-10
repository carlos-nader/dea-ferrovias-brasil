# 01 — Correlação TKU × Receita

Script: `R/01_correlacao_tku_receita.R`
Output: `output/01_correlacao_tku_receita/`

---

## Objetivo

Testar se TKU (Tonelada-Quilômetro Útil) e receita operacional bruta são variáveis
redundantes para fins de DEA. Critério: se r > 0,90 (Pearson), a receita é descartada
e o período de análise permanece 2006–2025 (apenas TKU). Se r ≤ 0,90, a receita
adiciona informação e deve ser considerada como variável de output, restringindo o
período a 2008–2024 (disponibilidade das Demonstrações Financeiras).

Teste realizado com dados da MRS Logística. Aplicação às demais DMUs fica
condicionada à decisão metodológica descrita na seção de limitações.

---

## Método

### Correlação de Pearson — e não regressão

A relação entre TKU e receita é **simétrica**: nenhuma das variáveis é dependente da
outra no sentido causal. O objetivo é verificar se as duas medem a mesma dimensão do
desempenho (redundância), não estimar um efeito ou fazer previsão. A regressão impõe
uma assimetria (variável dependente × independente) que não existe aqui. O coeficiente
de Pearson r mede a associação linear sem pressupor direcionalidade, sendo o
instrumento correto para o teste de redundância.

### Limiar r > 0,90

Critério usual na literatura de DEA para identificar outputs redundantes: se r > 0,90,
as duas variáveis capturam essencialmente a mesma informação e incluir ambas no modelo
não acrescenta poder discriminatório — podendo até distorcer os scores por colinearidade.
Abaixo desse limiar, as variáveis medem dimensões distintas do desempenho e a inclusão
de ambas é metodologicamente justificada.

---

## Dados utilizados

### TKU

- Fonte: Anuário Estatístico ANTT
- Arquivo: `data/MRS/anuario_mrs_2025.xlsx`, aba `2.1.2`, coluna `Total`
- Período: 2008–2024
- Unidade: TKU (valor absoluto)

### Receita operacional bruta

- Fonte: notas explicativas às demonstrações financeiras encaminhadas à ANTT
- Acesso: <https://www.gov.br/antt/pt-br/assuntos/ferrovias/concessoes-ferroviarias>
  (pasta de cada concessionária → Demonstrações Financeiras)
- Arquivo: `data/MRS/df_mrs_receita.csv` (extração manual, 2008–2024)
- Unidade: R$ mil (valores nominais)
- Padrão contábil: IFRS

### Deflator

- Fonte: BCB SGS série 433 (IPCA variação % mensal, IBGE)
- Arquivo: `data/ipca_anual.csv` (gerado por `R/00_download_ipca.R`)
- Índice utilizado: índice médio anual (base jan/2008 = 100)
- Metodologia: ver `docs/00_download_ipca.md`

---

## Deflação

Para deflacionar a receita nominal (variável de fluxo anual), aplica-se o índice
médio anual do IPCA — nível médio de preços do ano, não a variação acumulada de
dezembro a dezembro:

```text
receita_real = receita_bruta × (indice_medio_2008 / indice_medio_ano)
```

Valores convertidos para R$ constantes de 2008.

---

## Resultado

| Estatística | Valor           |
|-------------|-----------------|
| Método      | Pearson         |
| Período     | 2008–2024 (MRS) |
| r           | **0,3156**      |

Correlação fraca: r ≤ 0,90. Pela regra definida, a receita adiciona informação
ao TKU e deveria ser incluída no DEA, restringindo o período a 2008–2024.

Outputs gerados:

- `output/01_correlacao_tku_receita/df_correlacao_mrs.csv` — tabela com TKU,
  receita nominal, deflator e receita real por ano
- `output/01_correlacao_tku_receita/plot_correlacao_mrs.png` — dispersão TKU ×
  receita real com reta de regressão

---

## Limitação identificada — composição da receita operacional bruta

A receita operacional bruta das concessionárias ferroviárias é composta por:

- **Receita de frete** — diretamente associada ao transporte de carga, output do
  serviço medido pelos inputs do DEA (locomotivas, vagões, trem-km)
- **Receita de serviços acessórios** — carregamento, descarregamento, manobras etc.;
  serviços complementares que não dependem exclusivamente dos ativos modelados como
  inputs

A receita alternativa (aluguéis, consultorias etc.) é categoria separada e não integra
a receita operacional bruta.

As Demonstrações Financeiras não apresentam a separação entre frete e acessório de
forma consistente entre concessionárias e ao longo dos anos: alguns DFs detalham as
duas rubricas separadamente; outros apresentam apenas o total operacional. Extrair
apenas a receita de frete exigiria o uso dos balancetes mensais da ANTT, que contêm
a abertura por conta contábil.

Incluir receita operacional bruta como output do DEA introduz uma variável
parcialmente desconectada dos inputs, comprometendo a consistência do modelo.

---

## Decisão pendente

Discutir com a orientadora (Profa. Dra. Maisa Sales Gama Tobias) e com o Prof.
Gildemir Ferreira da Silva:

1. **Descartar receita** — usar apenas TKU; período 2006–2025; modelo DEA mais limpo
2. **Extrair receita de frete via balancetes** — metodologicamente ideal, pois os
   balancetes contêm abertura por conta contábil; porém os dados encaminhados pelas
   concessionárias à ANTT não são públicos (acesso a avaliar)
3. **Manter receita operacional bruta** — aceitar a limitação explicitamente na
   metodologia do TCC

O teste com a MRS permanece no repositório como registro do processo de decisão
metodológica, independentemente da conclusão.
