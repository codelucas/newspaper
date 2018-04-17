# -*- coding: utf-8 -*-
"""
Anything that has to do with threading in this library
must be abstracted in this file. If we decide to do gevent
also, it will deserve its own gevent file.
"""
__title__ = 'newspaper'
__author__ = 'Lucas Ou-Yang'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014, Lucas Ou-Yang'

from concurrent.futures import ThreadPoolExecutor, wait
from threading import Lock

from .configuration import Configuration

def perform_download_articles(paper):
    return paper.download_articles

class ThreadPool:
    def __init__(self, num_threads, timeout_seconds=0):
        self.mutex = Lock()
        self.executor = ThreadPoolExecutor(max_workers=num_threads)
        self.timeout_seconds = timeout_seconds
        self.futures = {}

    def add_task(self, func, *args, **kargs):
        """
        Adds the given task, and returns a future for the completion.
        """
        f = self.executor.submit(func, *args, **kargs)

        f.add_done_callback(self._remove_future)

        self.mutex.acquire()
        try:
            self.futures[f] = 1
        finally:
            self.mutex.release()

        return f

    def _remove_future(self, f):
        self.mutex.acquire()
        try:
            self.futures.pop(f, None)
        finally:
            self.mutex.release()

    def wait_completion(self):
        """
        Waits for the completion of every submitted task.
        Note: this will block insertion of new tasks while waiting.
        """

        self.mutex.acquire()
        try:
            wait(self.futures, timeout=self.timeout_seconds)
        finally:
            self.mutex.release()
            self.futures = {}




class NewsPool(object):

    def __init__(self, config=None):
        """
        Abstraction of a threadpool. A newspool can accept any number of
        source OR article objects together in a list. It allocates one
        thread to every source and then joins.

        We allocate one thread per source to avoid rate limiting.
        5 sources = 5 threads, one per source.

        >>> import newspaper
        >>> from newspaper import news_pool

        >>> cnn_paper = newspaper.build('http://cnn.com')
        >>> tc_paper = newspaper.build('http://techcrunch.com')
        >>> espn_paper = newspaper.build('http://espn.com')

        >>> papers = [cnn_paper, tc_paper, espn_paper]
        >>> news_pool.set(papers)
        >>> news_pool.join()

        # All of your papers should have their articles html all populated now.
        >>> cnn_paper.articles[50].html
        u'<html>blahblah ... '
        """
        self.papers = {}
        self.pool = None
        self.config = config or Configuration()

    def join(self):
        """
        Waits for all submitted papers to complete downloading their articles.
        """
        if self.pool is None:
            print('Call set(..) with a list of source '
                  'objects before .join(..)')
            raise

        # Wait for completion of all futures.
        self.pool.wait_completion()

    def set(self, paper_list, num_threads=8, fun=perform_download_articles):
        """
        Adds all of the given papers to the NewsPool.
        They will have their articles downloaded in parallel.
        Returns a dictionary mapping each future to the newspaper that it is downloading
        articles for.
        """
        self.pool = ThreadPool(num_threads)
        self.papers = { self.pool.add_task(fun(paper)): paper for paper in paper_list }
        return self.papers
