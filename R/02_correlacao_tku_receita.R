library(dplyr)
library(ggplot2)

# ── 1. IPCA ──────────────────────────────────────────────────────────────────
ipca <- read.csv("data/ipca_mensal.csv") |>
  mutate(
    ano = as.integer(format(as.Date(date), "%Y")),
    mes = as.integer(format(as.Date(date), "%m"))
  ) |>
  select(ano, mes, indice)

# ── 2. DMUs ──────────────────────────────────────────────────────────────────
dmus <- list(
  list(sigla = "EFC",       pasta = "data/EFC"),
  list(sigla = "EFVM",      pasta = "data/EFVM"),
  list(sigla = "FERROESTE", pasta = "data/FERROESTE"),
  list(sigla = "FCA",       pasta = "data/FCA"),
  list(sigla = "FNS",       pasta = "data/FNS"),
  list(sigla = "FTC",       pasta = "data/FTC"),
  list(sigla = "FTL",       pasta = "data/FTL"),
  list(sigla = "MRS",       pasta = "data/MRS"),
  list(sigla = "RMN",       pasta = "data/RMN"),
  list(sigla = "RMO",       pasta = "data/RMO"),
  list(sigla = "RMP",       pasta = "data/RMP"),
  list(sigla = "RMS",       pasta = "data/RMS")
)

dir.create("output/02_correlacao_tku_receita",
           recursive = TRUE, showWarnings = FALSE)

# ── 3. Loop por DMU ──────────────────────────────────────────────────────────
resultados <- list()

for (dmu in dmus) {
  s <- tolower(dmu$sigla)

  tku <- read.csv(file.path(dmu$pasta, paste0(s, "_tku_mensal.csv")))

  receita <- read.csv(
    file.path(dmu$pasta, paste0(s, "_receita_siref.csv"))
  ) |>
    group_by(ano, mes) |>
    summarise(receita_nominal = sum(receita_rs), .groups = "drop")

  df <- tku |>
    inner_join(receita, by = c("ano", "mes")) |>
    inner_join(ipca,    by = c("ano", "mes")) |>
    mutate(
      receita_real = receita_nominal / (indice / 100),
      data         = as.Date(sprintf("%d-%02d-01", ano, mes))
    ) |>
    arrange(data) |>
    mutate(dmu = dmu$sigla)

  r <- cor(df$tku, df$receita_real, method = "pearson", use = "complete.obs")
  cat(sprintf("%-12s r = %.4f  (%d obs)\n", dmu$sigla, r, nrow(df)))

  resultados[[dmu$sigla]] <- list(df = df, r = r)

  # -- Plot dual-eixo --
  sf <- max(df$receita_real, na.rm = TRUE) / max(df$tku, na.rm = TRUE)

  p <- ggplot(df, aes(x = data)) +
    geom_line(aes(y = tku * sf,    color = "TKU"),         linewidth = 0.7) +
    geom_line(aes(y = receita_real, color = "Receita real"), linewidth = 0.7) +
    scale_y_continuous(
      name   = "Receita real (R$ bilhões, base jan/2012)",
      labels = function(x) sprintf("%.1f", x / 1e9),
      sec.axis = sec_axis(
        ~ . / sf,
        name   = "TKU (bilhões)",
        labels = function(x) sprintf("%.1f", x / 1e9)
      )
    ) +
    scale_color_manual(
      values = c("TKU" = "#2166ac", "Receita real" = "#d6604d")
    ) +
    scale_x_date(date_breaks = "2 years", date_labels = "%Y") +
    labs(
      title    = sprintf("%s — TKU e Receita Real (2012–2025)",
                         dmu$sigla),
      subtitle = sprintf(
        "Receita deflacionada pelo IPCA (base: jan/2012)  |  r = %.4f", r
      ),
      x = NULL, color = NULL
    ) +
    theme_minimal(base_size = 12) +
    theme(legend.position = "bottom")

  ggsave(
    sprintf("output/02_correlacao_tku_receita/plot_%s.png", s),
    plot = p, width = 10, height = 5, dpi = 150
  )
}

# ── 4. Poolado ───────────────────────────────────────────────────────────────
dados_todos <- bind_rows(lapply(resultados, function(x) x$df))

r_poolado <- cor(dados_todos$tku, dados_todos$receita_real,
                 method = "pearson", use = "complete.obs")
cat(sprintf("%-12s r = %.4f  (%d obs)\n", "POOLADO", r_poolado,
            nrow(dados_todos)))

# ── 5. Tabela mensal completa ─────────────────────────────────────────────────
tabela <- dados_todos |>
  select(dmu, ano, mes, tku, receita_nominal, indice, receita_real) |>
  arrange(dmu, ano, mes)

write.csv(tabela,
          "output/02_correlacao_tku_receita/dados_mensais.csv",
          row.names = FALSE)

# ── 6. Tabela de correlações ──────────────────────────────────────────────────
corr_tab <- bind_rows(
  lapply(names(resultados), function(nm) {
    data.frame(
      dmu       = nm,
      r_pearson = resultados[[nm]]$r,
      n_obs     = nrow(resultados[[nm]]$df)
    )
  }),
  data.frame(dmu = "POOLADO", r_pearson = r_poolado,
             n_obs = nrow(dados_todos))
)

write.csv(corr_tab,
          "output/02_correlacao_tku_receita/correlacoes.csv",
          row.names = FALSE)

cat("\n")
print(corr_tab, row.names = FALSE)
cat("\nResultados salvos em output/02_correlacao_tku_receita/\n")
