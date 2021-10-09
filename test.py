from newspaper import Article

url = 'https://economictimes.indiatimes.com/mf/analysis/what-is-ideal-mutual-fund-portfolio-for-me/articleshow/86833812.cms'
article = Article(url)
article.download()
article.parse()

print(article.publish_date)