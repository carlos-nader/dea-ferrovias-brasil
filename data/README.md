# data/

A maioria dos arquivos desta pasta não está versionada no repositório.
Para reproduzir as análises, baixe os arquivos indicados abaixo e salve aqui.
Exceções versionadas: `ipca_anual.csv`, `ipca_mensal.csv` e `df_[sigla]_receita.csv`.

## Deflator — IPCA (versionado)

Fonte: Banco Central do Brasil · SGS série 433 (IPCA variação % mensal, IBGE)
Gerado por: `R/00_download_ipca.R` · Cobertura: **2008–2024**

| Arquivo            | Conteúdo                                              |
|--------------------|-------------------------------------------------------|
| `ipca_mensal.csv`  | Variação % mensal e índice acumulado (base jan/2008)  |
| `ipca_anual.csv`   | Variação acumulada anual (%) e índice médio anual     |

Metodologia e decisões: ver `docs/00_download_ipca.md`.

## Anuário Estatístico ANTT

Fonte: <https://www.gov.br/antt/pt-br/assuntos/ferrovias/anuario-estatistico-ferroviario>

Cobertura disponível: **2006–2025**

Baixar os arquivos Excel anuais de cada concessionária. Tabelas utilizadas:

| Tabela | Variável                                     |
|--------|----------------------------------------------|
| 2.1.1  | TU — Toneladas úteis transportadas           |
| 2.1.2  | TKU — Toneladas-quilômetro úteis             |
| 2.3.3  | Trem-quilômetro                              |
| 2.4.1  | Locomotivas em circulação                    |
| 2.4.2  | Disponibilidade e utilização de locomotivas  |
| 2.4.5  | Consumo de combustível (CCL)                 |
| 2.5.1  | Vagões em circulação                         |
| 2.5.2  | Disponibilidade e utilização de vagões       |

## Demonstrações Financeiras das Concessionárias

Fonte: <https://www.gov.br/antt/pt-br/assuntos/ferrovias/concessoes-ferroviarias>
(Para cada concessionária, acessar a pasta correspondente → Demonstrações Financeiras)

Cobertura disponível: **2008–2024** (2025 pendente de publicação) · Padrão IFRS
Variável de interesse: receita operacional bruta extraída das notas explicativas às
demonstrações financeiras encaminhadas à ANTT.

Dados extraídos manualmente e salvos como `df_[sigla]_receita.csv` por concessionária.
Estrutura, unidade e decisões metodológicas: ver `docs/01_correlacao_tku_receita.md`.

## Estrutura de pastas

```text
data/
├── ipca_mensal.csv               (versionado)
├── ipca_anual.csv                (versionado)
└── [sigla]/
    ├── anuario_[sigla]_[ano].xlsx    ex: anuario_mrs_2025.xlsx
    ├── df_[sigla]_[ano].pdf          ex: df_mrs_2024.pdf
    └── df_[sigla]_receita.csv        ex: df_mrs_receita.csv (versionado)
```
