# Projects
Repo for personal projects

## Wildfire - R
Pulls current wildfire spatial data for preprocessing and plotting. The map is created using RMarkdown for viewing in your browser.
To generate the wildfire tracking map, run scripts in following order:  
1.) fires pipeline.R   
2.) wildfire map.Rmd  

Schedule jobs to automatically pull new wildfire data and refresh map, run scripts in following order:  
1.) knit wildfire map.R  
2.) schedule scripts.R  

## IMDb Top 250 - Python
Webscraping the IMDb Top 250 movies page for categorical and numerical data to be transformed into dataset and saved out as a csv.  
These data include:  
- Rank
- Name
- Year
- Director
- Cast
- Rating
- Number of reviews

## Scraping Census Data - R
Webscraping the Census page for residential housing starts in 2019 as part of a research paper.
