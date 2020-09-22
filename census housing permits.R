library(tigris)
library(ggplot2)
library(ggthemes)
library(rgeos)
library(sp)
library(dplyr)
library(rvest)

# County borders to plot
counties <- ggplot2::map_data("county", c("oregon", "washington", "montana", "idaho"))

# All roads in US - will filter down later
road <- primary_roads()

# for ggplot, we need to simplify the lines otherwise it'll take
# forever to plot. however, gSimplify whacks the SpatialLinesDataFrame
# so we need to re-bind the data from the original object to it so
# we can use "fortify"

roads_simp <- gSimplify(road, tol=1/200, topologyPreserve=TRUE)
roads_simp <- SpatialLinesDataFrame(roads_simp, road@data)
roads_simp <- roads_simp[roads_simp@data$FULLNAME == "I- 5",]

roads_map <- fortify(roads_simp)

# Taking min/max so I-5 is easier to visualize
i_five_coord <- counties %>%
  summarize(lat_min = min(lat),
            lat_max = max(lat),
            long_min = min(long),
            long_max = max(long))

# Filter for I-5 to highlight housing starts along I-5 corridor
roads_map <- roads_map %>% 
  filter(dplyr::between(long, i_five_coord$long_min, i_five_coord$long_max)) %>%
  filter(dplyr::between(lat, i_five_coord$lat_min, i_five_coord$lat_max))

# Test plot
ggplot() +
  geom_polygon(data = counties, aes(x = long, y = lat, group = group), color = "black", fill = "grey", alpha = .5) + 
  geom_polygon(data = roads_map %>% 
                 filter(dplyr::between(long, i_five_coord$long_min, i_five_coord$long_max)) %>%
                 filter(dplyr::between(lat, i_five_coord$lat_min, i_five_coord$lat_max)),
           aes(x = long, y = lat, group = group),
           color = "red", fill = "white", size = 0.25) +
  coord_map() +
  theme_map()

counties <- counties %>%
  group_by(region, subregion) %>%
  mutate(west = ifelse(min(long) <= mean(roads_map$long) + .65, "West", "East"))
table(counties$west)

state_boundary <- map_data("state") %>%
  filter(region %in% c("oregon", "washington", "montana", "idaho"))
        
# Check east/west assignments
ggplot() +
  geom_polygon(data = state_boundary, aes(x = long, y = lat, group = group), color = "black", fill = NA, size = 1) +
  geom_polygon(data = counties, aes(x = long, y = lat, group = group, fill = factor(west)), color = "black", alpha = .5, size = .5) + 
  geom_polygon(data = roads_map,
                aes(x = long, y = lat, group = group),
                color = "red", fill = "white", size = 0.5) +
  coord_map() +
  theme_map() +
  theme(legend.position = "right") +
  guides(fill = guide_legend(title = ""))

west_cty <- counties %>%
  filter(west == "West") %>%
  select(region, subregion) %>%
  unique()

# 2018 Census data
census <- read.csv("~/Desktop/ACEEE 2020/CensusData.csv", stringsAsFactors = FALSE, skip = 1)
colnames(census) <- gsub("[[:punct:]]", "", colnames(census))
census <- census %>%
  select(GeographicAreaName, contains("hous")) %>%
  tidyr::separate(col = GeographicAreaName, into = c("County", "State"), sep = ", ")

state_totals <- census %>%
  filter(County %in% c("Idaho", "Montana", "Oregon", "Washington")) %>%
  group_by(State = County) %>%
  summarize(HousingUnits = format(sum(EstimateTotalhousingunits), big.mark = ","))

census <- census %>%
  filter(County %in% c("Idaho", "Montana", "Oregon", "Washington") == FALSE)

census <- census %>%
  mutate(County = tolower(gsub(" County", "", County)),
         State = tolower(State))
table(census$County %in% counties$subregion)
n_distinct(counties$subregion)

counties <- counties %>%
  left_join(census %>%
              group_by(County, State) %>%
              summarize(HousingUnits = sum(EstimateTotalhousingunits)),
            by = c("region" = "State", "subregion" = "County"))

# Plot 2018 housing starts
ggplot() +
  geom_polygon(data = state_boundary, aes(x = long, y = lat, group = group), color = "black", fill = NA, size = 1) +
  geom_polygon(data = counties, aes(x = long, y = lat, group = group, fill = HousingUnits), color = "black", alpha = .5, size = .5) +
  scale_fill_gradient(low = "light blue", high = "red", limits = c(10000, 700000)) +
  geom_polygon(data = roads_map,
               aes(x = long, y = lat, group = group),
               color = "red", fill = "red", size = 0.5) +
  coord_map() +
  theme_map() +
  theme(legend.position = "right") +
  guides(fill = guide_legend(title = "Housing Starts"))

housing_starts <- counties %>%
  group_by(region, subregion, west) %>% 
  summarize(HousingStarts = unique(HousingUnits)) %>%
  ungroup() %>%
  mutate(group = ifelse(region %in% c("oregon", "washington"), "OR_WA", "ID_MT")) %>%
  group_by(region) %>%
  summarize(HousingStarts = format(sum(HousingStarts, na.rm = TRUE), big.mark = ","))
housing_starts

# ---- Web scraping census.gov -----
# From 2019 quick facts table
counties <- counties %>%
  mutate(county_string = paste0(subregion, "county", region))

census_housing_permits <- tibble()
for(county in unique(counties$county_string)){
  county_url <- gsub(" ", "", county)
  county_url <- gsub("national", "", county_url)

  census_url <- paste0('https://www.census.gov/quickfacts/fact/table/', county_url)
  census_webpage <- read_html(census_url)
  census_nodes <- html_nodes(census_webpage, 'tr')[[32]]
  housing_permits <- html_text(census_nodes)
  housing_permits <- gsub("Building permits, 2019", "", housing_permits)
  housing_permits <- gsub("\n", "", housing_permits, fixed = TRUE)
  housing_permits <- gsub(",", "", housing_permits)
  housing_permits <- gsub(" ", "", housing_permits)
  housing_permits <- as.numeric(housing_permits)

  state_county_permits <- tibble(
    county = county,
    housing_permits_est = housing_permits
  )

  census_housing_permits <- bind_rows(census_housing_permits, state_county_permits)
  print(county)
}

census_data <- census_housing_permits %>%
  mutate(county = gsub("county", ", ", county)) %>%
  tidyr::separate(col = county, into = c("county", "state"), sep = ", ")

county_housing_permits <- counties %>%
  select(-HousingUnits) %>%
  left_join(census_data, by = c("subregion" = "county", "region" = "state"))

county_housing_permits %>%
  group_by(region, subregion, west) %>%
  summarize(counts = unique(housing_permits_est)) %>%
  mutate(group = ifelse(region %in% c("oregon", "washington"), "OR_WA", "ID_MT")) %>%
  group_by(region) %>%
  summarize(counts = format(sum(counts, na.rm = TRUE), big.mark = ","))

# Final heatmap for paper
ggplot() +
  geom_polygon(data = state_boundary, aes(x = long, y = lat, group = group), color = "black", fill = NA, size = 1) +
  geom_polygon(data = county_housing_permits, aes(x = long, y = lat, group = group, fill = housing_permits_est), color = "black", alpha = .5, size = .5) +
  scale_fill_gradient(low = "light blue", high = "red", breaks = c(100, 5000, 10000, 15000), labels = c("100", "5,000", "10,000", "15,000"), na.value = "white") +
  geom_polygon(data = roads_map,
               aes(x = long, y = lat, group = group),
               color = "red", fill = "red", size = 0.5) +
  coord_map() +
  theme_map() +
  theme(legend.position = c(.7,.1),
        legend.text = element_text(size = 18),
        legend.title = element_text(size = 18)) +
  guides(fill = guide_legend(title = "Housing Starts"))

