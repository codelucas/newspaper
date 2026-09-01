from newspaper import Article

url = 'https://timesofindia.indiatimes.com/city/meerut/a-week-after-farmers-deaths-union-ministers-son-arrested/articleshow/86899674.cms'
article = Article(url)
article.download()
article.parse()

print(article.publish_date)