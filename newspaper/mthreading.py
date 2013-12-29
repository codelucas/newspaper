# -*- coding: utf-8 -*-
"""
Anything that has to do with threading in this library
must be abstracted in this file. If we decide to do gevent
also, it will deserve its own gevent file.
"""
import Queue
from threading import Thread

class Worker(Thread):
    """
    Thread executing tasks from a given tasks queue
    """
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
                print 'thread breaking b/c queue is empty'
                break
            try:
                func(*args, **kargs)
            except Exception, e:
                print 'critical multi-thread err %s' % e

            self.tasks.task_done()

class ThreadPool:
    """
    Pool of threads consuming tasks from a queue
    """
    def __init__(self, num_threads):
        self.tasks = Queue.Queue(num_threads)
        for _ in range(num_threads):
            Worker(self.tasks)

    def add_task(self, func, *args, **kargs):
        """
        Add a task to the queue
        """
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """
        Wait for completion of all the tasks in the queue
        """
        self.tasks.join()

    def clear_threads(self):
        """
        """
        pass

class NewsPool(object):
    def __init__(self):
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
        >>> news_pool.go()

        # all of your papers should have their articles html all populated now.
        >>> cnn_paper.articles[50].html
        u'<html>blahblah ... '

        """
        self.papers = []

    def go(self):
        """
        runs the mtheading and returns when all threads have joined
        """
        self.pool.wait_completion()

    def set(self, paper_list):
        """
        sets the job batch
        """
        self.papers = paper_list
        self.pool = ThreadPool(len(self.papers))

        for paper in self.papers:
            self.pool.add_task(paper.download_articles)




