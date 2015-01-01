import os
import sys
import traceback

TEST_DIR = os.path.abspath(os.path.dirname(__file__))
PARENT_DIR = os.path.join(TEST_DIR, '..')
sys.path.insert(0, PARENT_DIR)

import newspaper
from newspaper.urls import get_domain


DOMAINS_FILE = os.path.join('data', 'fulltext_domain_list.txt')
URLS_FILE = os.path.join('data', 'fulltext_url_list.txt')


def get_base_domain(url):
    """For example, the base url of uk.reuters.com => reuters.com
    """
    domain = get_domain(url)
    end_chunks = domain.split('.')[-2:]
    base_domain = '.'.join(end_chunks)
    return base_domain


with open(DOMAINS_FILE, 'r') as f:
    domains = ['http://' + d.strip() for d in f.readlines()
               if d.strip()]


with open(URLS_FILE, 'a') as f:
    for domain in domains:
        print('on domain', domain)

        try:
            paper = newspaper.build(domain)
        except Exception:
            print('domain %s has failed!' % domain)
            traceback.print_exc()
            continue

        if paper.size() < 2:
            print('domain %s has < 2 articles, skipping' % domain)
            continue

        written = 0
        for article in paper.articles:
            if get_base_domain(article.url) == domain[len('http://'):]:
                f.write(article.url + '\n')
                written += 1
                if written == 2:
                    break

        if written != 2:
            print('domain %s does not have >= 2 valid urls' % domain)
