library(rbcb)
library(dplyr)

# BCB SGS série 433 — IPCA variação % mensal (IBGE)
ipca_mensal <- get_series(433, start_date = "2008-01-01", end_date = "2024-12-31")
names(ipca_mensal)[2] <- "ipca_mensal_pct"

# Índice mensal acumulado (base: jan/2008 = 100)
fator <- 1 + ipca_mensal$ipca_mensal_pct / 100
ipca_mensal$indice <- round(100 * cumprod(fator) / fator[1], 4)

write.csv(ipca_mensal, "data/ipca_mensal.csv", row.names = FALSE)

# Resumo anual: variação acumulada (dez a dez) e índice médio anual
# Índice médio é o deflator correto para variáveis de fluxo (receita anual)
ipca_anual <- ipca_mensal |>
  mutate(ano = as.integer(format(date, "%Y"))) |>
  group_by(ano) |>
  summarise(
    ipca_acum_pct = round((prod(1 + ipca_mensal_pct / 100) - 1) * 100, 2),
    indice_medio  = round(mean(indice), 4),
    .groups = "drop"
  )

write.csv(ipca_anual, "data/ipca_anual.csv", row.names = FALSE)

cat("Arquivos salvos:\n")
cat("  data/ipca_mensal.csv —", nrow(ipca_mensal), "linhas\n")
cat("  data/ipca_anual.csv  —", nrow(ipca_anual), "linhas\n")
print(ipca_anual)
