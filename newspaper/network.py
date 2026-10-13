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


FAIL_ENCODING = 'ISO-8859-1'


def get_request_kwargs(timeout, useragent, proxies, headers):
    """This Wrapper method exists b/c some values in req_kwargs dict
    are methods which need to be called every time we make a request
    """
    return {
        'headers': headers if headers else {'User-Agent': useragent},
        'cookies': cj(),
        'timeout': timeout,
        'allow_redirects': True,
        'proxies': proxies
    }


def get_html(url, config=None, response=None):
    """HTTP response code agnostic
    """
    try:
        return get_html_2XX_only(url, config, response)
    except requests.exceptions.RequestException as e:
        log.debug('get_html() error. %s on URL: %s' % (e, url))
        return ''


def get_html_2XX_only(url, config=None, response=None):
    """Consolidated logic for http requests from newspaper. We handle error cases:
    - Attempt to find encoding of the html by using HTTP header. Fallback to
      'ISO-8859-1' if not provided.
    - Error out if a non 2XX HTTP response code is returned.
    """
    config = config or Configuration()
    useragent = config.browser_user_agent
    timeout = config.request_timeout
    proxies = config.proxies
    headers = config.headers

    if response is not None:
        return _get_html_from_response(response, config)

    response = requests.get(
        url=url, **get_request_kwargs(timeout, useragent, proxies, headers))

    html = _get_html_from_response(response, config)

    if config.http_success_only:
        # fail if HTTP sends a non 2XX response
        response.raise_for_status()

    # Check to see if the Content-Type header exists
    mime_type = None
    if 'content-type' in response.headers:
        mime_type = response.headers.get('content-type').split(';')[0]

    # return html
    return ArticleResponseWrapper(html, mime_type)


def _get_html_from_response(response, config):
    if response.headers.get('content-type') in config.ignored_content_types_defaults:
        return config.ignored_content_types_defaults[response.headers.get('content-type')]
    if response.encoding != FAIL_ENCODING:
        # return response as a unicode string
        html = response.text
    else:
        html = response.content
        if 'charset' not in response.headers.get('content-type'):
            encodings = requests.utils.get_encodings_from_content(response.text)
            if len(encodings) > 0:
                response.encoding = encodings[0]
                html = response.text

    return html or ''


class MRequest(object):
    """Wrapper for request object for multithreading. If the domain we are
    crawling is under heavy load, the self.resp will be left as None.
    If this is the case, we still want to report the url which has failed
    so (perhaps) we can try again later.
    """
    def __init__(self, url, config=None):
        self.url = url
        self.config = config
        config = config or Configuration()
        self.useragent = config.browser_user_agent
        self.timeout = config.request_timeout
        self.proxies = config.proxies
        self.headers = config.headers
        self.resp = None

    def send(self):
        try:
            self.resp = requests.get(self.url, **get_request_kwargs(
                self.timeout, self.useragent, self.proxies, self.headers))
            if self.config.http_success_only:
                self.resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            log.critical('[REQUEST FAILED] ' + str(e))

class ArticleResponseWrapper(object):
    """Wrapper for returning html and mime type from the various
    download methods. This should be treated as a simple DTO and
    not used directly, as the values will be populated on the
    Article itself.
    """
    def __init__(self, html, mime_type):
        self.html = html
        self.mime_type = mime_type



def multithread_request(urls, config=None):
    """Request multiple urls via mthreading, order of urls & requests is stable
    returns same requests but with response variables filled.
    """
    config = config or Configuration()
    num_threads = config.number_threads
    timeout = config.thread_timeout_seconds

    pool = ThreadPool(num_threads, timeout)

    m_requests = []
    for url in urls:
        m_requests.append(MRequest(url, config))

    for req in m_requests:
        pool.add_task(req.send)

    pool.wait_completion()
    return m_requests

