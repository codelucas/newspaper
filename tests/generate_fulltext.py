import os
import sys
import traceback

TEST_DIR = os.path.abspath(os.path.dirname(__file__))
PARENT_DIR = os.path.join(TEST_DIR, '..')
sys.path.insert(0, PARENT_DIR)

from newspaper import Article
from newspaper.urls import get_domain


FULLTEXT_OUTPUT_PREFIX = os.path.join('data', 'text')
URLS_FILE = os.path.join('data', 'fulltext_url_list.txt')


def get_base_domain(url):
    """For example, the base url of uk.reuters.com => reuters.com
    """
    domain = get_domain(url)
    tld = '.'.join(domain.split('.')[-2:])
    if tld in ['co.uk', 'com.au', 'al.com']:  # edge cases
        end_chunks = domain.split('.')[-3:]
    else:
        end_chunks = domain.split('.')[-2:]
    base_domain = '.'.join(end_chunks)
    return base_domain


with open(URLS_FILE, 'r') as f:
    urls = [d.strip() for d in f.readlines() if d.strip()]


domain_counters = {}

for url in urls:
    domain = get_base_domain(url)
    if domain in domain_counters:
        domain_counters[domain] += 1
    else:
        domain_counters[domain] = 1

    print('URL:', url, 'Domain:', str(domain_counters[domain]))
    filename = domain + str(domain_counters[domain]) + '.txt'
    filename = os.path.join(FULLTEXT_OUTPUT_PREFIX, filename)
    try:
        a = Article(url)
        a.download()
        a.parse()
        out_text = a.text
    except Exception:
        print('URL: %s has failed!' % url)
        traceback.print_exc()
        out_text = ''

    with open(filename, 'w') as f:
        f.write(out_text)
