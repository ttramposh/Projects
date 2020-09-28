# Import packages
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import numpy as np

imdb_url = 'https://www.imdb.com/chart/top/?ref_=nv_mv_250'
imdb_r = requests.get(imdb_url)
imdb_html = imdb_r.text
print(imdb_html)

imdb_soup = BeautifulSoup(imdb_html)
print(imdb_soup)

#imdb_pretty_soup = imdb_soup.prettify()
#print(imdb_pretty_soup)

top_250_movies = []
for movie in imdb_soup.findAll('tr')[1:250]:
    details = movie.find('td', attrs = {'class':'titleColumn'})

    rank = int(str(details.next).strip().replace(".", ""))
    name = details.find('a').next
    year = details.find('span', attrs = {'class':'secondaryInfo'}).next.replace("(", "").replace(")", "")
    people = details.find('a')['title'].split(sep = " (dir.), ")
    director = people[0]
    cast = people[1]

    movie_ratings = movie.find('td', attrs = {'class':'ratingColumn imdbRating'})
    rating = float(movie_ratings.find('strong').next)
    reviews = int(movie_ratings.find('strong')['title'].split(sep = "on ")[1].split(sep = " user")[0].replace(",", ""))

    movie_list = []
    movie_list.append([rank, name, year, director, cast, rating, reviews])

    top_250_movies.append(movie_list)

print(top_250_movies)
flatten = lambda l: [item for sublist in l for item in sublist]
df = pd.DataFrame(flatten(top_250_movies), columns = ['Rank', 'Movie', 'Year', 'Director', 'Cast', 'Rating', 'Reviews'])
print(df)

#df.to_csv('imdb_top_movies.csv')

# Find weighted average ratings of directors with more than 1 movie in the top 250
dir_movies = df.groupby('Director')['Movie'].nunique()
dir_ratings = df.groupby('Director').apply(lambda x: np.average(x['Rating'], weights = x['Reviews']))
dir_ratings.name = 'Rating'

dir_summary = pd.merge(dir_movies, dir_ratings, on = 'Director', how = 'left')
dir_summary = dir_summary[dir_summary['Movie'] > 1]

# Subset to top 10 directors
dir_summary = dir_summary.sort_values('Movie', ascending = False)[0:10]
dir_summary['Director'] = dir_summary.index
dir_summary = dir_summary.sort_values('Rating', ascending = False)

import seaborn as sns
import matplotlib.pyplot as plt

# Visualize director rankings
barplot = sns.barplot(x = 'Director', y = 'Rating', data = dir_summary)
barplot.set(ylim = (7, 9))
plt.xticks(rotation = 45)