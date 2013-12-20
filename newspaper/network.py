# -*- coding: utf-8 -*-

import logging
import requests
import math

from threading import activeCount
from .settings import cj
from .utils import chunks, ThreadPool, print_duration, get_useragent
# from .packages import grequests # use overridden modified version

log = logging.getLogger(__name__)

def get_request_kwargs(timeout):
    """wrapper method because some values in this dictionary are methods
    which need to be called every time we make a request"""

    return {
        #'headers' : {'User-Agent': get_useragent()},
        'cookies' : cj(),
        'timeout' : timeout,
        'allow_redirects' : True
    }

def get_html(url, response=None, timeout=7):
    """retrieves the html for either a url or a response object"""

    if response is not None:
        return response.text
    try:
        html = requests.get(url=url, **get_request_kwargs(timeout)).text
        if html is None:
            html = u''
        return html
    except Exception, e:
        # print '[REQUEST FAILED]', str(e)
        # log.debug('%s on %s' % (e, url))
        return u''

def sync_request(urls_or_url, timeout=7):
    """wrapper for a regular request, no asyn nor multithread"""

    if isinstance(urls_or_url, list):
        resps = [requests.get(url, **get_request_kwargs(timeout)) for url in urls_or_url]
        return resps
    else:
        return requests.get(urls_or_url, **get_request_kwargs(timeout))

class MRequest(object):
    """
    Wrapper for request object for multithreading.
    If the domain we are crawling is under heavy load,
    the self.resp will be left as None. If this is the case,
    we still want to report the url which has failed so (perhaps)
    we can try again later.

    """

    def __init__(self, url, **req_kwargs):
        self.url = url
        self.req_kwargs = req_kwargs
        self.resp = None

    def send(self):
        try:
            self.resp = requests.get(self.url, **self.req_kwargs)
        except Exception, e:
            pass
            log.critical('[REQUEST FAILED] ' + str(e))
            # print '[REQUEST FAILED]', str(e) # TODO, do something with url when we fail!
            # leave the response as None

def multithread_request(urls, timeout=7, num_threads=10):
    """request multiple urls via mthreading, order of urls & requests is stable
    returns same requests but with response variables filled"""

    pool = ThreadPool(num_threads)
    responses = []
    # print 'beginning of mthreading, %s threads running' % activeCount()

    m_requests = []
    for url in urls:
        m_requests.append(MRequest(url, **get_request_kwargs(timeout)))

    for req in m_requests:
        pool.add_task(req.send)

    pool.wait_completion()
    return m_requests

# def async_request(urls, timeout=7):
#    """receives a list of requests and sends them all
#    asynchronously at once"""
#
#    rs = (grequests.request('GET', url, **get_request_kwargs(timeout)) for url in urls)
#    responses = grequests.map(rs, size=10)
#
#    return responses

