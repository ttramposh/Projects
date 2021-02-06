from newsapi import NewsApiClient
import json
import pandas as pd
from datetime import datetime as dt, timedelta
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.multiclass import OneVsRestClassifier
from sklearn.linear_model import LogisticRegression
import yaml

# Consider using NLP to score positive vs negative news about specific stock

# Init
with open("keys.yml", "r") as stream:
    try:
        api_key_dict = yaml.safe_load(stream)
        api_key = list(api_key_dict.values())[0]
    except yaml.YAMLError as exc:
        print(exc)

news_api = NewsApiClient(api_key=api_key)

# Pull
today = dt.today()
t_delta = timedelta(30)
from_date = (today - t_delta).strftime('%Y-%m-%d')
to_date = today.strftime('%Y-%m-%d')

msft_news = news_api.get_everything(
    q = "microsoft",
    from_param = from_date,
    to = to_date,
    language = "en"
)

print(msft_news)

# Reduce
article_dict = {a: k for a, k in msft_news.items() if a.startswith('articles')}
print(article_dict)

# convert
j_data = json.dumps(article_dict)
msft_json = json.loads(j_data)
msft_json['articles']

# Dataframe
msft_news_df = pd.DataFrame.from_dict(pd.json_normalize(msft_json['articles']), orient="columns")

# Summary
msft_news_df.head()
msft_news_df.columns

msft_news_df.\
    groupby(['author'])['title'].\
    nunique().\
    sort_values(ascending=False)

msft_news_df['publishedAt'].agg({'min', 'max'})

# Mutate clean date
msft_news_df['timestamp'] = msft_news_df['publishedAt']
msft_news_df['timestamp'] = msft_news_df['timestamp'].astype('str')
msft_news_df['timestamp'] = msft_news_df['timestamp'].apply(lambda t: t[0:10])
msft_news_df['timestamp'] = msft_news_df['timestamp'].apply(lambda t: dt.strptime(t, '%Y-%m-%d'))

#msft_news_df.to_csv('msft_news_jan21.csv')

# --- NLP ---
msft_news_df = pd.read_csv('msft_df_merged.csv')
msft_news_df.columns
msft_news_df = msft_news_df.drop(
    ['Unnamed: 0.1', 'Unnamed: 0', 'url', 'urlToImage',
     'publishedAt', 'Open', 'High', 'Low', 'Close',
     'Volume', 'Dividends', 'Stock Splits', 'month',
     'm_avg_month', 'm_avg_30', 'm_avg_200', 'yday_close',
     'yday_open', 'yday_low', 'yday_high', 'price_change',
     'pct_change', 'content'],
    axis=1
)

msft_news_df = msft_news_df.dropna()

categorize_label = lambda x: x.astype('category')
msft_news_df = msft_news_df.apply(categorize_label, axis = 0)
print(msft_news_df.dtypes)

label_dummies = pd.get_dummies(msft_news_df)

# Create token pattern
token_alphanum = '[A-Za-z0-9]+(?=\\s+)'

# Instantiate CountVec
vec_alphanum = CountVectorizer(token_pattern=token_alphanum)

# Fit to data
vec_alphanum.fit(msft_news_df['description'])

# Print num of tokens
msg = "There are {} tokens if we split on non-alpha numeric"
print(msg.format(len(vec_alphanum.get_feature_names())))
print(vec_alphanum.get_feature_names()[:20])

labels = msft_news_df.columns.to_list()
print(labels)

# Def combine_text_cols function
def combine_text_cols(df, to_drop):
    """
    Converts all text in each row of df to single vec
    """
    #to_drop = set(to_drop) & set(df.columns.tolist())
    text_data = df.drop(to_drop, axis = 1)

    # Join text items in row that have a space in between
    text_data = text_data.apply(lambda x: " ".join(x), axis = 1)

    return text_data

msft_news_df['text'] = combine_text_cols(msft_news_df[['description', 'author', 'title', 'timestamp']], to_drop='timestamp')
print(msft_news_df['text'][1])
#msft_news_df['text'] = msft_news_df['text'].apply(lambda x: ' '.join(x.split()))

# Replace col names in strings
#for word in labels:
#    msft_news_df['text'] = [str.replace(word, '') for str in msft_news_df['text']]

# Fit
vec_alphanum.fit_transform(msft_news_df['text'])

# Tokens
print("There are {} tokens in df".format(len(vec_alphanum.get_feature_names())))

# Remove stop words - need to change all text to lower
## also looks like issue with creating 'text' column
msft_news_df['text'][1]
stopwords = pd.read_csv('stop_words.csv')
stopwords = stopwords['i'].to_list()

msft_news_df['text'] = msft_news_df['text'].apply(lambda x: " ".join([word for word in x.split() if word not in stopwords]))
#msft_news_df['text'].apply(lambda x: [word for word in x.split(" ") if word not in stopwords])[1]
msft_news_df['text'][1]


# Split
X_train, X_test, y_train, y_test = train_test_split(
    msft_news_df['text'],
    pd.get_dummies(msft_news_df['positive_change']),
    random_state=42
)

# Pipeline
pipeline = Pipeline([
    ('vec', CountVectorizer()),
    ('clf', OneVsRestClassifier(LogisticRegression()))
])

# Fit to training data
pipeline.fit(X_train, y_train)

# Accuracy
accuracy = pipeline.score(X_test, y_test)
print("Accuracy on data:", accuracy)

