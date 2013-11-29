# -*- coding: utf-8 -*-

import logging
import requests
import grequests

from .settings import cj, USERAGENT

log = logging.getLogger(__name__)

def get_html(url, response=None, timeout=7):
    """retrieves the html for either a url or a response object"""

    if response is not None:
        return response.text
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
        return html
    except Exception, e:
        log.debug('%s on %s' % (e, url))
        return u''

def async_request(urls, timeout=7):
    """receives a list of requests and sends them all
    asynchronously at once"""

    req_kwargs = {
        'headers' : {'User-Agent': USERAGENT},
        'cookies' : cj(),
        'timeout' : timeout,
        'allow_redirects' : True
    }
    rs = (grequests.request('GET', url, **req_kwargs) for url in urls)
    responses = grequests.map(rs) # send all requests at once async
    return responses