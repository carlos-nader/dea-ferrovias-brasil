library(rbcb)
library(dplyr)

# BCB SGS série 433 — IPCA variação % mensal (IBGE)
ipca_mensal <- get_series(
  433, start_date = "2012-01-01", end_date = "2025-12-31"
)
names(ipca_mensal)[2] <- "ipca_mensal_pct"

# Índice mensal acumulado (base: jan/2012 = 100)
# Jan/2012 é o primeiro mês da série SIREF — ponto de partida da análise
fator <- 1 + ipca_mensal$ipca_mensal_pct / 100
ipca_mensal$indice <- round(100 * cumprod(fator) / fator[1], 4)

write.csv(ipca_mensal, "data/ipca_mensal.csv", row.names = FALSE)

cat("Arquivo salvo:\n")
cat("  data/ipca_mensal.csv —", nrow(ipca_mensal), "linhas\n")
print(ipca_mensal)
