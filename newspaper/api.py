# -*- coding: utf-8 -*-

from .source import Source

def build(url=u''):
    """returns a constructed source object without
    downloading or parsing the articles"""

    url = url or '' # empty string precedence over None
    valid_href = ('://' in url) and (url[:4] == 'http')

    if not valid_href:
        print 'ERR: provide valid url'
        return None

    return 'hello world'

