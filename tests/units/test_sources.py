# -*- coding: utf-8 -*-

from newspaper.sources import Sources
import datetime

def get_content(url, language):
    webpage = Sources(url, language=language)
    articles = webpage.get_articles()
    categories = webpage.get_categories()
    return articles, categories

# noinspection PyUnresolvedReferences
def test_newspaper_cnn():
    articles, categories = get_content("https://www.cnn.com", language='en')
    # assert len(articles)
    assert len(categories)


# noinspection PyUnresolvedReferences
def test_newspaper_yahoo():
    articles, categories = get_content("https://www.yahoo.com", language='en')
    assert len(articles)
    assert len(categories)

# noinspection PyUnresolvedReferences
def test_newspaper_sina_cn():
    articles, categories = get_content("https://www.sina.com.cn", language='zh')
    assert len(articles)
    assert len(categories)
    # for article in articles:
    #     print(article)
    # for category in categories:
    #     print(category)

def test_article_cn():
    url = "http://www.bbc.co.uk/zhongwen/simp/chinese_news/2012/12/121210_hongkong_politics.shtml"
    webpage = Sources(url, language='zh')
    article = webpage.get_article()
    assert len(article.title)
    assert isinstance(article.publish_date, datetime.datetime)
    # assert len(article.authors)
    assert len(article.summary)
    assert len(article.keywords)
    assert len(article.text)
    assert len(article.html)
