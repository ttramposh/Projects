# Import packages
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.linear_model import Lasso, LinearRegression
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import mean_squared_error


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
    first_actor = cast.split(sep = ",")[0]
    second_actor = cast.split(sep = ", ")[1]

    movie_ratings = movie.find('td', attrs = {'class':'ratingColumn imdbRating'})
    rating = float(movie_ratings.find('strong').next)
    reviews = int(movie_ratings.find('strong')['title'].split(sep = "on ")[1].split(sep = " user")[0].replace(",", ""))

    movie_list = []
    movie_list.append([rank, name, year, director, first_actor, second_actor, rating, reviews])

    top_250_movies.append(movie_list)

print(top_250_movies)
flatten = lambda l: [item for sublist in l for item in sublist]
df = pd.DataFrame(flatten(top_250_movies), columns = ['Rank', 'Movie', 'Year', 'Director', 'First_Actor', 'Second_Actor', 'Rating', 'Reviews'])
print(df)

# Write out data as csv
#df.to_csv('imdb_top_movies.csv')

# Read in imdb top 250 data
df = pd.read_csv('imdb_top_movies.csv')
df = df.drop('Unnamed: 0', axis = 1)

# Find weighted average ratings of directors with more than 1 movie in the top 250
dir_movies = df.groupby('Director')['Movie'].nunique()
dir_ratings = df.groupby('Director').apply(lambda x: np.average(x['Rating'], weights = x['Reviews']))
dir_ratings.name = 'Rating'

dir_merge = pd.merge(dir_movies, dir_ratings, on = 'Director', how = 'left')
dir_summary = dir_merge[dir_merge['Movie'] > 1]

# Subset to top 10 directors
dir_summary = dir_summary.sort_values('Movie', ascending = False)[0:10]
dir_summary['Director'] = dir_summary.index
dir_summary = dir_summary.sort_values('Rating', ascending = False)

# Visualize director rankings
barplot = sns.barplot(x = 'Director', y = 'Rating', data = dir_summary)
barplot.set(ylim = (7, 9))
plt.xticks(rotation = 45)

# Convert categorical vars to dummies
df.describe()
df.columns
df.info()

year_range = df['Year'].max() - df['Year'].min()
print(year_range)

df['year_bin'] = np.nan
df.loc[df['Year'] < 1950, 'year_bin'] = "< 1950"
df.loc[(df['Year'] >= 1950) & (df['Year'] < 1960), 'year_bin'] = "1950 to 1959"
df.loc[(df['Year'] >= 1960) & (df['Year'] < 1970), 'year_bin'] = "1960 to 1969"
df.loc[(df['Year'] >= 1970) & (df['Year'] < 1980), 'year_bin'] = "1970 to 1979"
df.loc[(df['Year'] >= 1980) & (df['Year'] < 1990), 'year_bin'] = "1980 to 1989"
df.loc[(df['Year'] >= 1990) & (df['Year'] < 2000), 'year_bin'] = "1990 to 1999"
df.loc[(df['Year'] >= 2000) & (df['Year'] < 2010), 'year_bin'] = "2000 to 2009"
df.loc[(df['Year'] >= 2010) & (df['Year'] <= 2020), 'year_bin'] = "2010 to 2020"

print(df['year_bin'])

#x = pd.get_dummies(df.drop(['Rank', 'Year', 'Movie', 'Rating'], axis = 1))
x = pd.get_dummies(df.drop(['Rank', 'year_bin', 'Movie', 'Rating'], axis = 1))
y = np.array(df['Rating']).reshape(-1,1)

# Split training and test sets
X_train, X_test, y_train, y_test = train_test_split(x, y, test_size= .2, random_state = 42)

# Hyperparameter tuning
param_grid = {'alpha': [50, 75, 100, 150, 250, 500, 1000, 3000, 5000, 10000, 100000]}

lasso = Lasso(tol = 0.001)
l_cv = GridSearchCV(lasso, param_grid, cv = 10)
l_cv.fit(X_train, y_train)
l_cv.best_params_
l_cv.best_score_

best_alpha = list(l_cv.best_params_.values())

# Lasso for feature(variable) selection
lasso = Lasso(alpha = best_alpha)
lasso_coef = lasso.fit(x, y).coef_
print(lasso_coef)

# Penalized vars
x_names = np.array(x.columns)
coef_tbl = np.concatenate((x_names.reshape(-1,1), lasso_coef.reshape(-1,1)), axis = 1)
vars_to_drop = coef_tbl[abs(coef_tbl[:,1]) == 0][:,0]

names = [c for c in x_names if not c in vars_to_drop]
print(names) # Lasso regression tells us that Reviews is not a significant predictor for Rating

# Plot
plt.plot(range(len(lasso_coef)), lasso_coef)
plt.xticks(range(len(x_names)), x_names, rotation = 90)
plt.ylabel('Coefficients')

# Lasso regression
lasso = Lasso(alpha = best_alpha)
lasso.fit(X_train, y_train)
y_pred = lasso.predict(X_test).reshape(-1,1)
lasso.score(X_test, y_test)

# RMSE
np.sqrt(mean_squared_error(y_test, y_pred))

# Plot predictions vs actual
plt.scatter(x = y_pred, y = y_test, color = 'blue')
plt.xlabel("Predicted Rating")
plt.ylabel("Actual Rating")
plt.title("IMDb Top 250 Movie Ratings")
