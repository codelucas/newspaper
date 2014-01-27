#!/bin/env python2.7

import lxml.html
import requests
from lxml.html.clean import Cleaner

cleaner = Cleaner()
cleaner.javascript = True
cleaner.style = True
cleaner.allow_tags = ['a', 'span', 'p', 'br', 'strong', 'b', 'em']
cleaner.remove_unknown_tags = False

html = requests.get('http://codelucas.com').text
doc = cleaner.clean_html(lxml.html.fromstring(html))

#print doc.text_content()


print lxml.html.tostring(doc)
