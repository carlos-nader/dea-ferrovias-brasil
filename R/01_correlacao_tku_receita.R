library(readxl)
library(dplyr)
library(ggplot2)

# --- TKU (Anuário ANTT, aba 2.1.2) ---
tku_raw <- read_excel(
  "data/MRS/anuario_mrs_2025.xlsx",
  sheet    = "2.1.2",
  skip     = 2,
  col_names = TRUE
)

tku <- tku_raw |>
  select(ano = 1, tku = 2) |>
  mutate(ano = suppressWarnings(as.integer(ano))) |>
  filter(!is.na(ano), ano >= 2008, ano <= 2024)

# --- Receita bruta (notas explicativas às DFs encaminhadas à ANTT) ---
# Unidade: R$ mil (valores nominais)
receita <- read.csv("data/MRS/df_mrs_receita.csv")

# --- Deflator (IPCA índice médio anual, base jan/2008 = 100) ---
ipca <- read.csv("data/ipca_anual.csv")
indice_base <- ipca$indice_medio[ipca$ano == 2008]

# --- Merge e deflação ---
df <- tku |>
  left_join(receita, by = "ano") |>
  left_join(ipca |> select(ano, indice_medio), by = "ano") |>
  mutate(
    receita_real = receita_bruta * (indice_base / indice_medio),
    tku_milhoes  = tku / 1e6
  )

# --- Correlação de Pearson ---
r <- cor(df$tku, df$receita_real, method = "pearson")

cat(sprintf("\nCorrelação de Pearson — MRS (2008–2024)\n"))
cat(sprintf("TKU × receita operacional bruta deflacionada\n"))
cat(sprintf("r = %.4f\n\n", r))

if (abs(r) > 0.90) {
  cat("r > 0,90: receita é redundante em relação ao TKU.\n")
  cat("Decisão: usar apenas TKU como proxy de output (período 2006–2025).\n")
} else {
  cat("r <= 0,90: receita adiciona informação ao TKU.\n")
  cat("Decisão: incluir receita no DEA (período 2008–2024).\n")
}

# --- Tabela de resultados ---
cat("\n")
print(df |> select(ano, tku_milhoes, receita_bruta, indice_medio, receita_real))

# --- Salvar resultados ---
dir.create("output/01_correlacao_tku_receita", recursive = TRUE, showWarnings = FALSE)

write.csv(
  df |> select(ano, tku, tku_milhoes, receita_bruta, indice_medio, receita_real),
  "output/01_correlacao_tku_receita/df_correlacao_mrs.csv",
  row.names = FALSE
)

# --- Scatter plot ---
p <- ggplot(df, aes(x = tku_milhoes, y = receita_real / 1e6)) +
  geom_point(size = 3) +
  geom_smooth(method = "lm", se = FALSE, linetype = "dashed", color = "gray40") +
  geom_text(aes(label = ano), vjust = -0.8, size = 3) +
  labs(
    title = sprintf("TKU × Receita real — MRS (2008–2024)  |  r = %.4f", r),
    x     = "TKU (milhões)",
    y     = "Receita bruta real (R$ milhões, base 2008)"
  ) +
  theme_minimal()

ggsave(
  "output/01_correlacao_tku_receita/plot_correlacao_mrs.png",
  plot = p, width = 8, height = 5, dpi = 150
)

cat("\nResultados salvos em output/01_correlacao_tku_receita/\n")
