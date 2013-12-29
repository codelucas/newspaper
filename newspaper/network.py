# -*- coding: utf-8 -*-
"""
"""
import logging
import requests

from .settings import cj
from .configuration import Configuration
from .mthreading import ThreadPool
# from .packages import grequests

log = logging.getLogger(__name__)
default_config = Configuration()

def get_request_kwargs(timeout, useragent):
    """
    wrapper method because some values in this dictionary are methods
    which need to be called every time we make a request
    """
    return {
        'headers' : {'User-Agent': useragent},
        'cookies' : cj(),
        'timeout' : timeout,
        'allow_redirects' : True
    }

def get_html(url, config=None, response=None):
    """
    retrieves the html for either a url or a response object
    """
    config = default_config if not config else config
    useragent = config.browser_user_agent
    timeout = config.request_timeout

    if response is not None:
        return response.text
    try:
        html = requests.get(url=url, **get_request_kwargs(timeout, useragent)).text
        if html is None:
            html = u''
        return html
    except Exception, e:
        # print '[REQUEST FAILED]', str(e)
        log.debug('%s on %s' % (e, url))
        return u''

def sync_request(urls_or_url, config=None):
    """
    wrapper for a regular request, no asyn nor multithread
    """
    config = default_config if not config else config
    useragent = config.browser_user_agent
    timeout = config.request_timeout
    if isinstance(urls_or_url, list):
        resps = [requests.get(url, **get_request_kwargs(timeout, useragent))
                                                for url in urls_or_url]
        return resps
    else:
        return requests.get(urls_or_url, **get_request_kwargs(timeout, useragent))

class MRequest(object):
    """
    Wrapper for request object for multithreading.
    If the domain we are crawling is under heavy load,
    the self.resp will be left as None. If this is the case,
    we still want to report the url which has failed so (perhaps)
    we can try again later.
    """
    def __init__(self, url, config=None):
        self.url = url
        config = default_config if not config else config
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
            # TODO, do something with url when we fail!
            # print '[REQUEST FAILED]', str(e)

def multithread_request(urls, config=None):
    """request multiple urls via mthreading, order of urls & requests is stable
    returns same requests but with response variables filled"""
    config = default_config if not config else config
    num_threads = config.number_threads

    pool = ThreadPool(num_threads)
    # print 'beginning of mthreading, %s threads running' % activeCount()

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
#    rs = (grequests.request('GET', url, **get_request_kwargs(timeout)) for url in urls)
#    responses = grequests.map(rs, size=10)
#
#    return responses

