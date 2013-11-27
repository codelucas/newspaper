# -*- coding: utf-8 -*-

import logging
import requests

from .settings import cj, USERAGENT

log = logging.getLogger(__name__)

def get_html(url, timeout=7):
    """downloads the html of a url"""

    try:
        req_kwargs = {
            'headers' : {'User-Agent': USERAGENT},
            'cookies' : cj(),
            'timeout' : timeout,
            'allow_redirects' : True
        }
        html = requests.get(url=url, **req_kwargs).text
        if html is None:
            return u''
    except Exception, e:
        log.debug('%s on %s' % (e, url))
        return u''
