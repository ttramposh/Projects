library(geojsonsf)
library(dplyr)
library(sp)

# Download wildfire perimeter data through NIFC API
wildfire_json <- geojson_sf("https://opendata.arcgis.com/datasets/5da472c6d27b4b67970acc7b5044c862_0.geojson")

# Extract spatial polygon objects from nested lists in 'geometry'
data <- tibble()
for(i in 1:nrow(wildfire_json)){
  for(j in 1:length(wildfire_json$geometry[[i]])){
    d <- wildfire_json[i,] %>%
      mutate(long = list(geometry[[1]][[j]][[1]][,1]),
             lat = list(geometry[[1]][[j]][[1]][,2]),
             group = paste0(i, "-", j))
    
    data <- rbind(data, d)
    print(paste0(i, "-", j))
  }
}

# Reclassify data - we cannot manipulate 'sf' object
data$geometry <- NULL
attr(data, "sf_column") <- NULL
attr(data, "sf_column")
data <- as.data.frame(data)

# Unnest coordinate points from lists
data <- data %>%  
  ungroup() %>%
  tidyr::unnest(cols = c(long, lat))

# Create polygon objects from lat, long coords then bind polygons with data. 
# End result is SpatialPolygonsDataFrame to use with leaflet
poly_convert <- lapply(unique(data$group), function(x){
  df = as.matrix(data[data$group == x, c("long", "lat")])
  polys = Polygons(list(Polygon(df)), ID = x)
  return(polys)})
data_polygon <- SpatialPolygons(poly_convert)
poly_ids <- sapply(slot(data_polygon, "polygons"), function(x) slot(x, "ID"))
poly_data_frame <- data.frame(ID = 1:length(data_polygon), row.names = poly_ids)
poly_data_frame <- SpatialPolygonsDataFrame(data_polygon, poly_data_frame)
poly_data_frame@data$newID <- rownames(poly_data_frame@data)
data <- data %>%
  ungroup() %>%
  select(-c(long, lat)) %>%
  mutate(OBJECTID = as.character(data$OBJECTID)) %>%
  group_by_all() %>%
  summarize(n = n())
poly_data_frame@data <- left_join(poly_data_frame@data, data, by = c("newID" = "group"))

# Save out R data for Rmarkdown script
save(poly_data_frame, file = 'wildfire_spatial_data.Rdata')
