# output/

Resultados gerados pelos scripts em `R/`. Uma subpasta por script, seguindo o
mesmo prefixo numérico.

## Versionamento

Nem todos os outputs são versionados. Subpastas que contenham dados derivados
de fontes não públicas (ex.: SIREF) estão no `.gitignore` e ficam apenas
localmente.

## Estrutura

```text
output/
└── [NN]_[nome-do-script]/
    ├── *.csv      Tabelas de resultados
    └── *.png      Gráficos
```

## Conteúdo atual

| Pasta                        | Script de origem                | Versionado | Conteúdo                                                             |
|------------------------------|---------------------------------|:----------:|----------------------------------------------------------------------|
| `02_correlacao_tku_receita/` | `R/02_correlacao_tku_receita.R` | Não        | Plots TKU × receita real por DMU; tabela mensal; correlações Pearson |
