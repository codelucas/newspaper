import os
import sys
import traceback

TEST_DIR = os.path.abspath(os.path.dirname(__file__))
PARENT_DIR = os.path.join(TEST_DIR, '..')
sys.path.insert(0, PARENT_DIR)

from newspaper import Article
from newspaper.urls import get_domain


HTML_FN = os.path.join(TEST_DIR, 'data/html')
URLS_FILE = os.path.join('data', 'fulltext_url_list.txt')


domain_counters = {}


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

for url in urls[50:]:
    domain = get_base_domain(url)
    if domain in domain_counters:
        domain_counters[domain] += 1
    else:
        domain_counters[domain] = 1

    try:
        a = Article(url)
        a.download()
    except Exception:
        print('<< URL: %s download ERROR >>' % url)
        traceback.print_exc()
        continue

    out_fn = domain + str(domain_counters[domain]) + '.html'
    out_fn = os.path.join(HTML_FN, out_fn)
    with open(out_fn, 'w') as f:
        f.write(a.html)

    print('mocked HTML for URL: %s' % url)
