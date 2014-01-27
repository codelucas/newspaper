import re
import sys
import os

TEST_DIR = os.path.abspath(os.path.dirname(__file__))
PARENT_DIR = os.path.join(TEST_DIR, '..')
sys.path.insert(0, PARENT_DIR)

from newspaper import Article

a = Article('http://arstechnica.com/information-technology/2014/01/quarkxpress-the-demise-of-a-design-desk-darling/', keep_article_html=True)
a.download()
a.parse()

m = re.findall('<h2', a.article_html, flags=re.I)

print a.article_html
print '\r\n'
print 'number of h2 tags', len(m), 'size of article_html', len(a.article_html)
