# -*- coding: utf-8 -*-
"""
All code involving requests and responses over the http network
must be abstracted in this file.
"""
__title__ = 'newspaper'
__author__ = 'Lucas Ou-Yang'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014, Lucas Ou-Yang'

import logging
import requests

from .configuration import Configuration
from .mthreading import ThreadPool
from .settings import cj

log = logging.getLogger(__name__)


def get_request_kwargs(timeout, useragent):
    """This Wrapper method exists b/c some values in req_kwargs dict
    are methods which need to be called every time we make a request
    """
    return {
        'headers': {'User-Agent': useragent},
        'cookies': cj(),
        'timeout': timeout,
        'allow_redirects': True
    }


def get_html(url, config=None, response=None):
    """Retrieves the html for either a url or a response object. All html
    extractions MUST come from this method due to some intricies in the
    requests module. To get the encoding, requests only uses the HTTP header
    encoding declaration requests.utils.get_encoding_from_headers() and reverts
    to ISO-8859-1 if it doesn't find one. This results in incorrect character
    encoding in a lot of cases.
    """
    FAIL_ENCODING = 'ISO-8859-1'
    config = config or Configuration()
    useragent = config.browser_user_agent
    timeout = config.request_timeout

    if response is not None:
        if response.encoding != FAIL_ENCODING:
            return response.text
        return response.content

    try:
        html = None
        response = requests.get(url=url,
                                **get_request_kwargs(timeout, useragent))
        if response.encoding != FAIL_ENCODING:
            html = response.text
        else:
            html = response.content
        if html is None:
            html = u''
        return html

    except Exception, e:
        log.debug('%s on %s' % (e, url))
        return u''


class MRequest(object):
    """Wrapper for request object for multithreading. If the domain we are
    crawling is under heavy load, the self.resp will be left as None.
    If this is the case, we still want to report the url which has failed
    so (perhaps) we can try again later.
    """
    def __init__(self, url, config=None):
        self.url = url
        config = config or Configuration()
        self.useragent = config.browser_user_agent
        self.timeout = config.request_timeout
        self.resp = None

    def send(self):
        try:
            self.resp = requests.get(self.url, **get_request_kwargs(
                                     self.timeout, self.useragent))
        except Exception, e:
            pass
            log.critical('[REQUEST FAILED] ' + str(e))


def multithread_request(urls, config=None):
    """Request multiple urls via mthreading, order of urls & requests is stable
    returns same requests but with response variables filled.
    """
    config = config or Configuration()
    num_threads = config.number_threads

    pool = ThreadPool(num_threads)

    m_requests = []
    for url in urls:
        m_requests.append(MRequest(url, config))

    for req in m_requests:
        pool.add_task(req.send)

    pool.wait_completion()
    return m_requests

# def async_request(urls, timeout=7):
#    """receives a list of requests and sends them all
#    asynchronously at once"""
#
#    rs = (grequests.request('GET', url,
#          **get_request_kwargs(timeout)) for url in urls)
#    responses = grequests.map(rs, size=10)
#
#    return responses


# def sync_request(urls_or_url, config=None):
#    """
#    Wrapper for a regular request, no asyn nor multithread.
#    """
#    # TODO config = default_config if not config else config
#    useragent = config.browser_user_agent
#    timeout = config.request_timeout
#    if isinstance(urls_or_url, list):
#        resps = [requests.get(url, **get_request_kwargs(timeout, useragent))
#                                                for url in urls_or_url]
#        return resps
#    else:
#        return requests.get(urls_or_url,
#                            **get_request_kwargs(timeout, useragent))
