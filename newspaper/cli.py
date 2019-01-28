import click

from newspaper import Article
from newspaper.utils import get_available_languages


@click.command()
@click.option('--language', '-l', default='en', help='Language in which the text is written',
              type=click.Choice(get_available_languages()))
@click.option('--url', '-u', help='URL to parse', required=True)
def parse(url, language):
    article = Article(url, language=language)
    article.download()
    article.parse()
    print(article.text)


if __name__ == '__main__':
    parse()
