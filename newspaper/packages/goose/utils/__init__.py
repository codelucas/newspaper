# -*- coding: utf-8 -*-
"""\
This is a python port of "Goose" orignialy licensed to Gravity.com
under one or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.

Python port was written by Xavier Grangier for Recrutae

Gravity.com licenses this file
to you under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import time
import hashlib
import re
import os
import goose
import codecs
import urlparse


class BuildURL(object):
    def __init__(self, url, finalurl=None):
        self.url = url
        self.finalurl = finalurl

    def getHostname(self, o):
        if o.hostname:
            return o.hotname
        elif self.finalurl:
            oo = urlparse(self.finalurl)
            if oo.hostname:
                return oo.hostname
        return None

    def getScheme(self, o):
        if o.scheme:
            return o.scheme
        elif self.finalurl:
            oo = urlparse(self.finalurl)
            if oo.scheme:
                return oo.scheme
        return 'http'

    def getUrl(self):
        """\

        """
        url_obj = urlparse(self.url)
        scheme = self.getScheme(url_obj)
        hostname = self.getHostname(url_obj)


class FileHelper(object):

    @classmethod
    def loadResourceFile(self, filename):
        if not os.path.isabs('filename'):
            dirpath = os.path.dirname(goose.__file__)
            path = os.path.join(dirpath, 'resources', filename)
        else:
            path = filename
        try:
            f = codecs.open(path, 'r', 'utf-8')
            content = f.read()
            f.close()
            return content
        except IOError:
            raise IOError("Couldn't open file %s" % path)


class ParsingCandidate(object):

    def __init__(self, urlString, link_hash):
        self.urlString = self.url = urlString
        self.link_hash = link_hash


class RawHelper(object):
    @classmethod
    def get_parsing_candidate(self, url, raw_html):
        if isinstance(raw_html, unicode):
            raw_html = raw_html.encode('utf-8')
        link_hash = '%s.%s' % (hashlib.md5(raw_html).hexdigest(), time.time())
        return ParsingCandidate(url, link_hash)


class URLHelper(object):
    @classmethod
    def get_parsing_candidate(self, url_to_crawl):
        # replace shebang is urls
        final_url = url_to_crawl.replace('#!', '?_escaped_fragment_=') \
                    if '#!' in url_to_crawl else url_to_crawl
        link_hash = '%s.%s' % (hashlib.md5(final_url).hexdigest(), time.time())
        return ParsingCandidate(final_url, link_hash)


class StringSplitter(object):
    """\

    """
    def __init__(self, pattern):
        self.pattern = re.compile(pattern)

    def split(self, string):
        if not string:
            return []
        return self.pattern.split(string)


class StringReplacement(object):

    def __init__(self, pattern, replaceWith):
        self.pattern = pattern
        self.replaceWith = replaceWith

    def replaceAll(self, string):
        if not string:
            return u''
        return string.replace(self.pattern, self.replaceWith)


class ReplaceSequence(object):

    def __init__(self):
        self.replacements = []

    #@classmethod
    def create(self, firstPattern, replaceWith=None):
        result = StringReplacement(firstPattern, replaceWith or u'')
        self.replacements.append(result)
        return self

    def append(self, pattern, replaceWith=None):
        return self.create(pattern, replaceWith)

    def replaceAll(self, string):
        if not string:
            return u''

        mutatedString = string

        for rp in self.replacements:
            mutatedString = rp.replaceAll(mutatedString)
        return mutatedString
