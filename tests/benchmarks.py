# -*- coding: utf-8 -*-
"""
Async IO vs multi-threading

Multi-thread:           5.9 secs (10 threads) for 100 requests
Async-IO with Gevent:   10.5 secs  for 100 requests
Single thread:          86.0 secs for 100 requests
"""
import sys
import logging
import queue
import os

from threading import activeCount
from threading import Thread
from http.cookiejar import CookieJar as cj
from .unit_tests import read_urls

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
log = logging.getLogger(__name__)

PARENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PARENT_DIR, '..'))

from newspaper.network import multithread_request, sync_request
from newspaper.utils import print_duration


@print_duration
def naive_run(urls):
    """no multithreading or async io
    """
    resps = []
    for url in urls:
        resps.append(sync_request(url))
    print(resps)


@print_duration
def mthread_run(urls):
    """download a bunch of urls via multithreading
    """
    reqs = multithread_request(urls)
    resps = [req.resp for req in reqs]


@print_duration
def asyncio_run(urls):
    """download a bunch of urls via async io
    """
    pass
    # rs = (grequests.request('GET', u, **req_kwargs) for u in urls)
    # responses = async_request(urls)
    # print(responses)


def benchmark():
    """multi-threading vs async-io vs regular
    """
    urls = read_urls(amount=1000)
    # naive_run(urls)
    mthread_run(urls)
    # asyncio_run(urls)


if __name__ == '__main__':
    benchmark()
