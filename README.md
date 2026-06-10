# dea-ferrovias-brasil

**Evolução da Eficiência Produtiva das Concessionárias Ferroviárias Brasileiras de Carga**
Análise Envoltória de Dados (DEA) · Período 2006–2024

TCC — Especialização em Engenharia Ferroviária · UFPA
Orientadora: Profa. Dra. Maisa Sales Gama Tobias (UFPA/ITEC)

---

## Problema de pesquisa

Como evoluiu a eficiência produtiva das concessionárias ferroviárias brasileiras de carga entre 2006 e 2024?

## Metodologia

- Modelos DEA CCR e BCC (output-oriented)
- Índice de Malmquist (evolução temporal)
- Bootstrap (Simar & Wilson 1998) para intervalos de confiança
- Software: R · pacote `Benchmarking` (Bogetoft & Otto 2011)

## Estrutura do repositório

```text
R/          Scripts de análise (numerados por etapa)
docs/       Documentação metodológica de cada script
data/       Dados brutos (não versionados — ver data/README.md)
output/     Resultados gerados pelos scripts (CSVs e plots)
```

## Reprodução

1. Clone o repositório
2. Baixe os arquivos de dados conforme `data/README.md`
3. Instale R >= 4.6.0 (r-project.org) e os pacotes necessários:

   ```r
   install.packages(c("rbcb", "readxl", "dplyr", "ggplot2", "Benchmarking"))
   ```

4. Execute os scripts em `R/` na ordem numérica

## Concessionárias Ferroviárias Federais

| Sigla | Nome | Uso no TCC |
| ----- | ---- | ---------- |
| EFC | Estrada de Ferro Carajás | DMU |
| EFVM | Estrada de Ferro Vitória a Minas | DMU |
| FCA | Ferrovia Centro-Atlântica | DMU |
| FTC | Ferrovia Tereza Cristina | DMU |
| FTL | Ferrovia Transnordestina (ex-CFN) | DMU |
| MRS | MRS Logística | DMU |
| RMN | Rumo Malha Norte | DMU |
| RMO | Rumo Malha Oeste | DMU |
| RMP | Rumo Malha Paulista | DMU |
| RMS | Rumo Malha Sul | DMU |
| FNS | Ferrovia Norte-Sul | Excluída* |
| RMC | Rumo Malha Central | Excluída* |
| TLSA | Ferrovia Transnordestina Logística | Excluída** |
| BAFER | Bahia Ferrovias | Excluída** |

\* Iniciou operações após 2006 — fora do período de análise.
\** Ferrovia em obras — sem operação comercial.

## Referências principais

- Silva et al. (2019). Medindo a eficiência produtiva do transporte por ferrovias brasileiras. *PPE/IPEA*, v.49 n.3.
- Marchetti & Wanke (2017). Brazil's rail freight transport efficiency analysis using two-stage DEA. *Transportation Research Part A*.
- Li & Hu (2010). DEA e Malmquist aplicados a ferrovias chinesas. *Journal of Information and Optimization Sciences*, v.31 n.5.
