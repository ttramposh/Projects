library(cronR)

# Pull wildfire spatial data
pull_script <- "fires pipeline.R"
pull_cmd <- cron_rscript(pull_script)
pull_cmd

cron_add(
  command = pull_cmd, 
  frequency = 'daily', 
  days_of_week = 'Mon', 
  at = '09:00', 
  id = 'fires_pipeline', 
  description = 'Pull wildfire perimeter data from NIFC'
)

# Re-knit html map with updated data
run_script <- "knit wildfire map.R"
run_cmd <- cron_rscript(run_script)
run_cmd

cron_add(
  command = run_cmd,
  frequency = 'daily',
  days_of_week = 'Mon',
  at = '9:15',
  id = 'wildfire_map',
  description = 'Knit wildfire map html'
)

cron_njobs()

# Clear scheduled jobs
cron_ls()
# cron_rm(id = "fires_pipeline")
# cron_rm(id = 'wildfire map')
cron_ls()
