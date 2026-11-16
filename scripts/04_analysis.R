# Statistical charts and simple summaries for Medicaid/CHIP enrollment.
# Run from the project root: Rscript scripts/04_analysis.R

suppressPackageStartupMessages({
  library(dplyr)
  library(ggplot2)
  library(readr)
})

root <- normalizePath(file.path(dirname(normalizePath(commandArgs(trailingOnly = FALSE)[4], mustWork = FALSE)), ".."), mustWork = FALSE)
# Fallback if commandArgs path is unreliable:
args <- commandArgs(trailingOnly = FALSE)
file_arg <- sub("^--file=", "", args[grepl("^--file=", args)])
if (length(file_arg) == 1) {
  root <- dirname(dirname(normalizePath(file_arg)))
} else {
  root <- getwd()
}

tables <- file.path(root, "output", "tables")
charts <- file.path(root, "output", "charts")
dir.create(charts, showWarnings = FALSE, recursive = TRUE)

co <- read_csv(file.path(tables, "measure_colorado_vs_baseline.csv"), show_col_types = FALSE)
nat <- read_csv(file.path(tables, "measure_national_vs_baseline.csv"), show_col_types = FALSE)
chg <- read_csv(file.path(tables, "measure_state_change_to_latest.csv"), show_col_types = FALSE)

co$period <- as.Date(co$period)
nat$period <- as.Date(nat$period)
# The raw file has an isolated 2013-09 month, then resumes in 2017-06.
# Plot from January 2020 so the pandemic rise and unwinding are visible without
# a straight line across the 2013-2017 reporting gap.
co_plot <- co %>% filter(period >= as.Date("2020-01-01"))
nat_plot <- nat %>% filter(period >= as.Date("2020-01-01"))

theme_set(theme_minimal(base_size = 12) + theme(plot.title = element_text(face = "bold", size = 13)))

# Colorado enrollment level
p1 <- ggplot(co_plot, aes(x = period, y = total_enrollment / 1e6)) +
  geom_line(color = "#1f4e79", linewidth = 1) +
  geom_vline(xintercept = as.Date("2023-04-01"), linetype = "dashed", color = "#c0504d") +
  labs(
    title = "Colorado Medicaid and CHIP enrollment",
    subtitle = "January 2020 through the latest month; dashed line marks April 2023, when unwinding began. July 2026 points are preliminary.",
    x = NULL, y = "Enrollees (millions)"
  )
ggsave(file.path(charts, "01_colorado_enrollment_level.png"), p1, width = 9, height = 5, dpi = 150)

# Percent change vs March 2023, Colorado and national
both <- bind_rows(
  co_plot %>% transmute(period, pct_change, series = "Colorado"),
  nat_plot %>% transmute(period, pct_change, series = "Sum of reporting states")
)
p2 <- ggplot(both, aes(x = period, y = pct_change, color = series)) +
  geom_line(linewidth = 1) +
  geom_hline(yintercept = 0, linewidth = 0.3) +
  geom_vline(xintercept = as.Date("2023-04-01"), linetype = "dashed", color = "gray40") +
  scale_color_manual(values = c("Colorado" = "#1f4e79", "Sum of reporting states" = "#7b2d8e")) +
  labs(
    title = "Percent change in Medicaid and CHIP enrollment since March 2023",
    subtitle = "January 2020 through the latest month; March 2023 = 0. July 2026 points are preliminary.",
    x = NULL, y = "Percent change from March 2023", color = NULL
  )
ggsave(file.path(charts, "02_pct_change_colorado_vs_national.png"), p2, width = 9, height = 5, dpi = 150)

# Distribution of state percent changes
p3 <- ggplot(chg, aes(x = pct_change)) +
  geom_histogram(bins = 15, fill = "#1f4e79", color = "white") +
  geom_vline(xintercept = chg$pct_change[chg$state == "CO"], color = "#c0504d", linewidth = 1) +
  labs(
    title = "State distribution of enrollment change from March 2023 to latest month",
    subtitle = "Red line: Colorado",
    x = "Percent change", y = "Number of states"
  )
ggsave(file.path(charts, "03_state_pct_change_distribution.png"), p3, width = 9, height = 5, dpi = 150)

# Largest declines
top <- chg %>% arrange(pct_change) %>% slice_head(n = 15)
p4 <- ggplot(top, aes(x = reorder(state_name, -pct_change), y = pct_change)) +
  geom_col(fill = "#1f4e79") +
  coord_flip() +
  labs(
    title = "15 states with the largest percent enrollment declines",
    subtitle = "From March 2023 to the latest month in the preferred series",
    x = NULL, y = "Percent change"
  )
ggsave(file.path(charts, "04_largest_state_declines.png"), p4, width = 9, height = 6, dpi = 150)

# Simple numeric summaries for the README (do not invent; written from tables)
co_m2023 <- co %>% filter(reporting_period == "202303")
co_last <- co %>% arrange(period) %>% slice_tail(n = 1)
nat_m2023 <- nat %>% filter(reporting_period == "202303")
nat_last <- nat %>% arrange(period) %>% slice_tail(n = 1)
sink(file.path(root, "output", "r_summary.txt"))
cat("Colorado March 2023 enrollment:", co_m2023$total_enrollment, "\n")
cat("Colorado latest period:", co_last$reporting_period, "enrollment:", co_last$total_enrollment, "pct_change:", co_last$pct_change, "\n")
cat("National March 2023 enrollment:", nat_m2023$total_enrollment, "states:", nat_m2023$states_with_total_enrollment, "\n")
cat("National latest period:", nat_last$reporting_period, "enrollment:", nat_last$total_enrollment, "pct_change:", nat_last$pct_change, "states:", nat_last$states_with_total_enrollment, "\n")
cat("Colorado rank by pct_change (1 = largest decline):\n")
chg2 <- chg %>% mutate(rank_decline = rank(pct_change, ties.method = "min"))
print(chg2 %>% filter(state == "CO"))
sink()
cat("Wrote R charts and output/r_summary.txt\n")
