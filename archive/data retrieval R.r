# 1-a.  Install the package once
install.packages("remotes")          # if you don’t have it
remotes::install_github("dutangc/CASdatasets")

# 1-b.  Load the dataset into memory
library(CASdatasets)
data(ausautoBI8999)                  # gives you a data.frame of 22 036 rows

library(lubridate)
df <- within(ausautoBI8999, {
  acc_date      <- as.Date(AccDate)
  rep_date      <- as.Date(ReportDate)
  fin_date      <- as.Date(FinDate)

  report_delay  <- as.integer(difftime(rep_date, acc_date,  units = "days"))
  payment_delay <- as.integer(difftime(fin_date, acc_date, units = "days"))
})

write.csv(df, "ausautoBI8999_prepped.csv", row.names = FALSE)