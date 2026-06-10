# output/

Resultados gerados pelos scripts em `R/`. Uma subpasta por script, seguindo o
mesmo prefixo numérico.

Os arquivos desta pasta são versionados no repositório.

## Estrutura

```text
output/
└── [NN]_[nome-do-script]/
    ├── df_*.csv      Tabelas de resultados
    └── plot_*.png    Gráficos
```

## Conteúdo atual

| Pasta                         | Script de origem                    | Conteúdo |
|-------------------------------|-------------------------------------|----------|
| `01_correlacao_tku_receita/`  | `R/01_correlacao_tku_receita.R`     | Correlação Pearson TKU × receita real — MRS (2008–2024) |
