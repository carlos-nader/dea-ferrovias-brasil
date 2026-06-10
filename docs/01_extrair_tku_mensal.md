# 01 — Extração de TKU mensal por concessionária

Script: `R/01_extrair_tku_mensal.R`
Outputs: `data/<DMU>/<dmu>_tku_mensal.csv` (um arquivo por concessionária)

---

## Fonte

Anuário Estatístico de Transportes Ferroviários — ANTT
Aba **2.1.2**: Produção Mensal de Transporte Ferroviário de Cargas, em
Tonelada-Quilômetro Útil (TKU).

Um arquivo Excel por concessionária, baixado manualmente do portal da ANTT:
<https://www.gov.br/antt/pt-br/assuntos/ferrovias/anuario-do-setor-ferroviario/arquivos-tabelas-excel>

Cobertura disponível: 2006 a 2025.

---

## Concessionárias extraídas (12 DMUs)

| Sigla      | Arquivo de entrada                            |
|------------|-----------------------------------------------|
| EFC        | `data/EFC/anuario_efc_2025.xlsx`              |
| EFVM       | `data/EFVM/anuario_efvm_2025.xlsx`            |
| FERROESTE  | `data/FERROESTE/anuario_ferroeste_2025.xlsx`  |
| FCA        | `data/FCA/anuario_fca_2025.xlsx`              |
| FNS        | `data/FNS/anuario_fns_2025.xlsx`              |
| FTC        | `data/FTC/anuario_ftc_2025.xlsx`              |
| FTL        | `data/FTL/anuario_ftl_2025.xlsx`              |
| MRS        | `data/MRS/anuario_mrs_2025.xlsx`              |
| RMN        | `data/RMN/anuario_rmn_2025.xlsx`              |
| RMO        | `data/RMO/anuario_rmo_2025.xlsx`              |
| RMP        | `data/RMP/anuario_rmp_2025.xlsx`              |
| RMS        | `data/RMS/anuario_rms_2025.xlsx`              |

A FTL inclui a série histórica anterior à cisão de 2013 (CFN → FTL + TLSA),
pois o Anuário trata a concessão como unidade contínua sob a sigla FTL.

---

## Layout da aba 2.1.2

```
Linha 1: título (célula mesclada)
Linha 2: subtítulo — "Produção Mensal... (milhões de TKU)"
Linha 3: cabeçalho — Ano | Total | Jan | Fev | ... | Dez
Linha 4+: dados anuais (2006, 2007, ...)
```

O `readxl` inicia leitura na primeira coluna não-vazia, descartando a coluna A
em branco do Excel. Com `skip = 3`, a leitura começa diretamente nos dados.

**Unidade:** os valores numéricos nas células estão em TKU (inteiros). A
expressão "milhões de TKU" no subtítulo refere-se à exibição formatada no
Excel, não ao valor armazenado na célula.

---

## Filtro temporal

O script filtra anos de **2012 a 2025** (168 meses por DMU), alinhando a
cobertura à série de receita disponível no SIREF.

---

## Estrutura do CSV de saída

| Coluna | Tipo     | Descrição                       |
|--------|----------|---------------------------------|
| `ano`  | inteiro  | Ano de referência               |
| `mes`  | inteiro  | Mês de referência (1 = janeiro) |
| `tku`  | numérico | TKU transportado no mês         |
