# -*- coding: utf-8 -*-

"""
Async IO vs multi-threading

Multi-thread:           30 secs (50 threads) for 50 requests
Async-IO with Gevent:   7 secs  for 50 requests
Single thread:          30 secs for 50 requests

"""

import logging
import Queue
import os
import requests
import grequests
import time

from threading import activeCount
from threading import Thread
from cookielib import CookieJar as cj

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
log = logging.getLogger(__name__)

PARENT_DIR = os.path.dirname(os.path.abspath(__file__))
URLS_FN = os.path.join(PARENT_DIR, 'sample_urls.txt')


class Worker(Thread):
    """Thread executing tasks from a given tasks queue"""

    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            try:
                func, args, kargs = self.tasks.get()
            except Queue.Empty:
                log.critical('thread breaking b/c queue is empty')
                break

            try:
                func(*args, **kargs)
            except Exception, e:
                log.critical('Critical multi-thread err %s' % e)

            self.tasks.task_done()


class ThreadPool:
    """Pool of threads consuming tasks from a queue"""
    def __init__(self, num_threads):
        self.tasks = Queue.Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()

    def clear_threads(self):
        """"""

def naive_run(urls, req_kwargs):
    """no multithreading or async io"""

    print('beginning batch job for naive run, %s threads running' % activeCount())
    responses = []
    for url in urls:
        responses.append(requests.get(url, **req_kwargs))
    print responses

def mthread_run(urls, req_kwargs):
    """download a bunch of urls via multithreading"""

    responses = []
    num_threads = 50
    pool = ThreadPool(num_threads)
    print('beginning batch job for mthreading, %s threads running' % activeCount())

    for url in urls:
        pool.add_task(responses.append(requests.get(url, **req_kwargs)))

    pool.wait_completion()
    print responses

def asyncio_run(urls, req_kwargs):
    """download a bunch of urls via async io"""

    print('beginning batch job for async io, %s threads running' % activeCount())
    # Create a set of unsent Requests
    rs = (grequests.request('GET', u, **req_kwargs) for u in urls)

    # Send them all at the same time
    responses = grequests.map(rs)
    print responses

def benchmark():
    """multi-threading vs async-io vs regular"""

    with open(URLS_FN, 'r') as f:
        urls = f.readlines()
        urls = [u.strip() for u in urls]

    req_kwargs = {
        'headers' : {'User-Agent': 'newspaper/0.0.1'},
        'cookies' : cj(),
        'timeout' : 10,
        'allow_redirects' : True
    }

    t1 = time.time()
    naive_run(urls, req_kwargs)
    t2 = time.time()
    print('naive run finished in %d seconds' % (t2-t1))

    # t3 = time.time()
    # asyncio_run(urls, req_kwargs)
    # t4 = time.time()
    # print('async io finished in %d seconds' % (t4-t3))

    # t5 = time.time()
    # mthread_run(urls, req_kwargs)
    # t6 = time.time()
    # print('multi-threading finished in %d seconds' % (t6-t5))


benchmark()