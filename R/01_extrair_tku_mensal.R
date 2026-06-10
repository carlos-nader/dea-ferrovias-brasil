library(readxl)

dmus <- list(
  list(sigla = "EFC",       pasta = "data/EFC",       arquivo = "anuario_efc_2025.xlsx"),
  list(sigla = "EFVM",      pasta = "data/EFVM",      arquivo = "anuario_efvm_2025.xlsx"),
  list(sigla = "FERROESTE", pasta = "data/FERROESTE", arquivo = "anuario_ferroeste_2025.xlsx"),
  list(sigla = "FCA",       pasta = "data/FCA",       arquivo = "anuario_fca_2025.xlsx"),
  list(sigla = "FNS",       pasta = "data/FNS",       arquivo = "anuario_fns_2025.xlsx"),
  list(sigla = "FTC",       pasta = "data/FTC",       arquivo = "anuario_ftc_2025.xlsx"),
  list(sigla = "FTL",       pasta = "data/FTL",       arquivo = "anuario_ftl_2025.xlsx"),
  list(sigla = "MRS",       pasta = "data/MRS",       arquivo = "anuario_mrs_2025.xlsx"),
  list(sigla = "RMN",       pasta = "data/RMN",       arquivo = "anuario_rmn_2025.xlsx"),
  list(sigla = "RMO",       pasta = "data/RMO",       arquivo = "anuario_rmo_2025.xlsx"),
  list(sigla = "RMP",       pasta = "data/RMP",       arquivo = "anuario_rmp_2025.xlsx"),
  list(sigla = "RMS",       pasta = "data/RMS",       arquivo = "anuario_rms_2025.xlsx")
)

extrair_tku <- function(caminho_xlsx) {
  # Aba 2.1.2: linhas 1-2 = títulos, linha 3 = cabeçalho, linha 4+ = dados
  # Colunas: [vazia] | Ano | Total | Jan | Fev | ... | Dez
  raw <- read_excel(caminho_xlsx, sheet = "2.1.2", skip = 3, col_names = FALSE)

  # readxl inicia na primeira coluna não-vazia (Ano), sem a col A em branco
  df <- raw[, 1:14]
  names(df) <- c("ano", "total", "jan", "fev", "mar", "abr", "mai",
                  "jun", "jul", "ago", "set", "out", "nov", "dez")

  df$ano <- suppressWarnings(as.integer(df$ano))
  df <- df[!is.na(df$ano) & df$ano >= 2012 & df$ano <= 2025, ]

  meses_nomes <- c("jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez")
  do.call(rbind, lapply(seq_len(nrow(df)), function(i) {
    data.frame(
      ano = df$ano[i],
      mes = 1:12,
      tku = as.numeric(unlist(df[i, meses_nomes]))
    )
  }))
}

for (dmu in dmus) {
  caminho <- file.path(dmu$pasta, dmu$arquivo)
  cat(sprintf("%-12s", dmu$sigla))
  tryCatch({
    df  <- extrair_tku(caminho)
    out <- file.path(dmu$pasta, paste0(tolower(dmu$sigla), "_tku_mensal.csv"))
    write.csv(df, out, row.names = FALSE)
    cat(sprintf("%d linhas -> %s\n", nrow(df), out))
  }, error = function(e) {
    cat("ERRO:", conditionMessage(e), "\n")
  })
}
