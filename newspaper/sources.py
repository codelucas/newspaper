#!/usr/bin/env python3


# noinspection PyPackageRequirements
from .article import Article
from .source import Source

class Sources:
    def __init__(self, url, language='en'):
        self.url = url
        self.language = language
        self.source = Source(url, language=language)
        self.source.download()
        self.source.parse()
        self.source.set_categories()
        self.source.download_categories()  # mthread
        self.source.parse_categories()
        self.source.generate_articles()

    def get_articles(self):
        # type: () -> list
        return self.source.article_urls()

    def get_categories(self):
        # type: () -> list
        return self.source.category_urls()

    def get_article(self):
        # type: () -> object
        article = Article(self.url, language=self.language)
        article.build()
        return article
