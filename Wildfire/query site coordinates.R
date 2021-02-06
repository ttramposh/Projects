library(dplyr)
library(RPostgreSQL)
library(DBI)

# Connect to db
database <- do.call(dbConnect, c(drv = dbDriver("PostgreSQL"), yaml::yaml.load_file("~/config.yml")$database))
dbListTables(database)

# Get lat/lon coordinates
site_coordinates <- dbGetQuery(
  database,
  "SELECT t_1.site_id, t_1.latitude, t_1.longitude, t_2.secondary_id
  FROM table_1 AS t_1
  INNER JOIN table_2 AS t_2 ON t_1.site_id = t_2.site_id"
)

# write.csv(site_coordinates, "/wildfire_site_coordinates.csv", row.names = FALSE)

# Disconnect from db
dbDisconnect(database);rm(database)
gc()
