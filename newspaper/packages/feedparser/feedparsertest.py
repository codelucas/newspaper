#!/usr/bin/env python
from newspaper.packages.feedparser import feedparser

__author__ = "Mark Pilgrim <http://diveintomark.org/>"
__license__ = """
Copyright (c) 2010-2013 Kurt McKee <contactme@kurtmckee.org>
Copyright (c) 2004-2008 Mark Pilgrim
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS 'AS IS'
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE."""

import codecs
import datetime
import glob
import operator
import os
import posixpath
import pprint
import re
import struct
import sys
import threading
import time
import unittest
import urllib
import warnings
import zlib
import BaseHTTPServer
import SimpleHTTPServer

if not feedparser._XML_AVAILABLE:
    sys.stderr.write('No XML parsers available, unit testing can not proceed\n')
    sys.exit(1)

try:
    # the utf_32 codec was introduced in Python 2.6; it's necessary to
    # check this as long as feedparser supports Python 2.4 and 2.5
    codecs.lookup('utf_32')
except LookupError:
    _UTF32_AVAILABLE = False
else:
    _UTF32_AVAILABLE = True

_s2bytes = feedparser._s2bytes
_l2bytes = feedparser._l2bytes

#---------- custom HTTP server (used to serve test feeds) ----------

_PORT = 8097 # not really configurable, must match hardcoded port in tests
_HOST = '127.0.0.1' # also not really configurable

class FeedParserTestRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    headers_re = re.compile(_s2bytes(r"^Header:\s+([^:]+):(.+)$"), re.MULTILINE)

    def send_head(self):
        """Send custom headers defined in test case

        Example:
        <!--
        Header:   Content-type: application/atom+xml
        Header:   X-Foo: bar
        -->
        """
        # Short-circuit the HTTP status test `test_redirect_to_304()`
        if self.path == '/-/return-304.xml':
            self.send_response(304)
            self.send_header('Content-type', 'text/xml')
            self.end_headers()
            return feedparser._StringIO(u''.encode('utf-8'))
        path = self.translate_path(self.path)
        # the compression tests' filenames determine the header sent
        if self.path.startswith('/tests/compression'):
            if self.path.endswith('gz'):
                headers = {'Content-Encoding': 'gzip'}
            else:
                headers = {'Content-Encoding': 'deflate'}
            headers['Content-type'] = 'application/xml'
        else:
            headers = dict([(k.decode('utf-8'), v.decode('utf-8').strip()) for k, v in self.headers_re.findall(open(path, 'rb').read())])
        f = open(path, 'rb')
        if (self.headers.get('if-modified-since') == headers.get('Last-Modified', 'nom')) \
            or (self.headers.get('if-none-match') == headers.get('ETag', 'nomatch')):
            status = 304
        else:
            status = 200
        headers.setdefault('Status', status)
        self.send_response(int(headers['Status']))
        headers.setdefault('Content-type', self.guess_type(path))
        self.send_header("Content-type", headers['Content-type'])
        self.send_header("Content-Length", str(os.stat(f.name)[6]))
        for k, v in headers.items():
            if k not in ('Status', 'Content-type'):
                self.send_header(k, v)
        self.end_headers()
        return f

    def log_request(self, *args):
        pass

class FeedParserTestServer(threading.Thread):
    """HTTP Server that runs in a thread and handles a predetermined number of requests"""

    def __init__(self, requests):
        threading.Thread.__init__(self)
        self.requests = requests
        self.ready = threading.Event()

    def run(self):
        self.httpd = BaseHTTPServer.HTTPServer((_HOST, _PORT), FeedParserTestRequestHandler)
        self.ready.set()
        while self.requests:
            self.httpd.handle_request()
            self.requests -= 1
        self.ready.clear()

#---------- dummy test case class (test methods are added dynamically) ----------
unicode1_re = re.compile(_s2bytes(" u'"))
unicode2_re = re.compile(_s2bytes(' u"'))

# _bytes is only used in everythingIsUnicode().
# In Python 2 it's str, and in Python 3 it's bytes.
_bytes = type(_s2bytes(''))

def everythingIsUnicode(d):
    """Takes a dictionary, recursively verifies that every value is unicode"""
    for k, v in d.iteritems():
        if isinstance(v, dict) and k != 'headers':
            if not everythingIsUnicode(v):
                return False
        elif isinstance(v, list):
            for i in v:
                if isinstance(i, dict) and not everythingIsUnicode(i):
                    return False
                elif isinstance(i, _bytes):
                    return False
        elif isinstance(v, _bytes):
            return False
    return True

def failUnlessEval(self, xmlfile, evalString, msg=None):
    """Fail unless eval(evalString, env)"""
    env = feedparser.parse(xmlfile)
    try:
        if not eval(evalString, globals(), env):
            failure=(msg or 'not eval(%s) \nWITH env(%s)' % (evalString, pprint.pformat(env)))
            raise self.failureException, failure
        if not everythingIsUnicode(env):
            raise self.failureException, "not everything is unicode \nWITH env(%s)" % (pprint.pformat(env), )
    except SyntaxError:
        # Python 3 doesn't have the `u""` syntax, so evalString needs to be modified,
        # which will require the failure message to be updated
        evalString = re.sub(unicode1_re, _s2bytes(" '"), evalString)
        evalString = re.sub(unicode2_re, _s2bytes(' "'), evalString)
        if not eval(evalString, globals(), env):
            failure=(msg or 'not eval(%s) \nWITH env(%s)' % (evalString, pprint.pformat(env)))
            raise self.failureException, failure

class BaseTestCase(unittest.TestCase):
    failUnlessEval = failUnlessEval

class TestCase(BaseTestCase):
    pass

class TestTemporaryFallbackBehavior(unittest.TestCase):
    "These tests are temporarily here because of issues 310 and 328"
    def test_issue_328_fallback_behavior(self):
        warnings.filterwarnings('error')

        d = feedparser.FeedParserDict()
        d['published'] = u'pub string'
        d['published_parsed'] = u'pub tuple'
        d['updated'] = u'upd string'
        d['updated_parsed'] = u'upd tuple'
        # Ensure that `updated` doesn't map to `published` when it exists
        self.assertTrue('published' in d)
        self.assertTrue('published_parsed' in d)
        self.assertTrue('updated' in d)
        self.assertTrue('updated_parsed' in d)
        self.assertEqual(d['published'], 'pub string')
        self.assertEqual(d['published_parsed'], 'pub tuple')
        self.assertEqual(d['updated'], 'upd string')
        self.assertEqual(d['updated_parsed'], 'upd tuple')

        d = feedparser.FeedParserDict()
        d['published'] = u'pub string'
        d['published_parsed'] = u'pub tuple'
        # Ensure that `updated` doesn't actually exist
        self.assertTrue('updated' not in d)
        self.assertTrue('updated_parsed' not in d)
        # Ensure that accessing `updated` throws a DeprecationWarning
        try:
            d['updated']
        except DeprecationWarning:
            # Expected behavior
            pass
        else:
            # Wrong behavior
            self.assertEqual(True, False)
        try:
            d['updated_parsed']
        except DeprecationWarning:
            # Expected behavior
            pass
        else:
            # Wrong behavior
            self.assertEqual(True, False)
        # Ensure that `updated` maps to `published`
        warnings.filterwarnings('ignore')
        self.assertEqual(d['updated'], u'pub string')
        self.assertEqual(d['updated_parsed'], u'pub tuple')
        warnings.resetwarnings()


class TestEverythingIsUnicode(unittest.TestCase):
    "Ensure that `everythingIsUnicode()` is working appropriately"
    def test_everything_is_unicode(self):
        self.assertTrue(everythingIsUnicode(
            {'a': u'a', 'b': [u'b', {'c': u'c'}], 'd': {'e': u'e'}}
        ))
    def test_not_everything_is_unicode(self):
        self.assertFalse(everythingIsUnicode({'a': _s2bytes('a')}))
        self.assertFalse(everythingIsUnicode({'a': [_s2bytes('a')]}))
        self.assertFalse(everythingIsUnicode({'a': {'b': _s2bytes('b')}}))
        self.assertFalse(everythingIsUnicode({'a': [{'b': _s2bytes('b')}]}))

class TestLooseParser(BaseTestCase):
    "Test the sgmllib-based parser by manipulating feedparser " \
    "into believing no XML parsers are installed"
    def __init__(self, arg):
        unittest.TestCase.__init__(self, arg)
        self._xml_available = feedparser._XML_AVAILABLE
    def setUp(self):
        feedparser._XML_AVAILABLE = 0
    def tearDown(self):
        feedparser._XML_AVAILABLE = self._xml_available

class TestStrictParser(BaseTestCase):
    pass

class TestMicroformats(BaseTestCase):
    pass

class TestEncodings(BaseTestCase):
    def test_doctype_replacement(self):
        "Ensure that non-ASCII-compatible encodings don't hide " \
        "disallowed ENTITY declarations"
        doc = """<?xml version="1.0" encoding="utf-16be"?>
        <!DOCTYPE feed [
            <!ENTITY exponential1 "bogus ">
            <!ENTITY exponential2 "&exponential1;&exponential1;">
            <!ENTITY exponential3 "&exponential2;&exponential2;">
        ]>
        <feed><title type="html">&exponential3;</title></feed>"""
        doc = codecs.BOM_UTF16_BE + doc.encode('utf-16be')
        result = feedparser.parse(doc)
        self.assertEqual(result['feed']['title'], u'&amp;exponential3')
    def test_gb2312_converted_to_gb18030_in_xml_encoding(self):
        # \u55de was chosen because it exists in gb18030 but not gb2312
        feed = u'''<?xml version="1.0" encoding="gb2312"?>
                  <feed><title>\u55de</title></feed>'''
        result = feedparser.parse(feed.encode('gb18030'), response_headers={
            'Content-Type': 'text/xml'
        })
        self.assertEqual(result.encoding, 'gb18030')

class TestFeedParserDict(unittest.TestCase):
    "Ensure that FeedParserDict returns values as expected and won't crash"
    def setUp(self):
        self.d = feedparser.FeedParserDict()
    def _check_key(self, k):
        self.assertTrue(k in self.d)
        self.assertTrue(hasattr(self.d, k))
        self.assertEqual(self.d[k], 1)
        self.assertEqual(getattr(self.d, k), 1)
    def _check_no_key(self, k):
        self.assertTrue(k not in self.d)
        self.assertTrue(not hasattr(self.d, k))
    def test_empty(self):
        keys = (
            'a','entries', 'id', 'guid', 'summary', 'subtitle', 'description',
            'category', 'enclosures', 'license', 'categories',
        )
        for k in keys:
            self._check_no_key(k)
        self.assertTrue('items' not in self.d)
        self.assertTrue(hasattr(self.d, 'items')) # dict.items() exists
    def test_neutral(self):
        self.d['a'] = 1
        self._check_key('a')
    def test_single_mapping_target_1(self):
        self.d['id'] = 1
        self._check_key('id')
        self._check_key('guid')
    def test_single_mapping_target_2(self):
        self.d['guid'] = 1
        self._check_key('id')
        self._check_key('guid')
    def test_multiple_mapping_target_1(self):
        self.d['summary'] = 1
        self._check_key('summary')
        self._check_key('description')
    def test_multiple_mapping_target_2(self):
        self.d['subtitle'] = 1
        self._check_key('subtitle')
        self._check_key('description')
    def test_multiple_mapping_mapped_key(self):
        self.d['description'] = 1
        self._check_key('summary')
        self._check_key('description')
    def test_license(self):
        self.d['links'] = []
        try:
            self.d['license']
            self.assertTrue(False)
        except KeyError:
            pass
        self.d['links'].append({'rel': 'license'})
        try:
            self.d['license']
            self.assertTrue(False)
        except KeyError:
            pass
        self.d['links'].append({'rel': 'license', 'href': 'http://dom.test/'})
        self.assertEqual(self.d['license'], 'http://dom.test/')
    def test_category(self):
        self.d['tags'] = []
        try:
            self.d['category']
            self.assertTrue(False)
        except KeyError:
            pass
        self.d['tags'] = [{}]
        try:
            self.d['category']
            self.assertTrue(False)
        except KeyError:
            pass
        self.d['tags'] = [{'term': 'cat'}]
        self.assertEqual(self.d['category'], 'cat')
        self.d['tags'].append({'term': 'dog'})
        self.assertEqual(self.d['category'], 'cat')

class TestOpenResource(unittest.TestCase):
    "Ensure that `_open_resource()` interprets its arguments as URIs, " \
    "file-like objects, or in-memory feeds as expected"
    def test_fileobj(self):
        r = feedparser._open_resource(sys.stdin, '', '', '', '', [], {})
        self.assertTrue(r is sys.stdin)
    def test_feed(self):
        f = feedparser.parse(u'feed://localhost:8097/tests/http/target.xml')
        self.assertEqual(f.href, u'http://localhost:8097/tests/http/target.xml')
    def test_feed_http(self):
        f = feedparser.parse(u'feed:http://localhost:8097/tests/http/target.xml')
        self.assertEqual(f.href, u'http://localhost:8097/tests/http/target.xml')
    def test_bytes(self):
        s = '<feed><item><title>text</title></item></feed>'.encode('utf-8')
        r = feedparser._open_resource(s, '', '', '', '', [], {})
        self.assertEqual(s, r.read())
    def test_string(self):
        s = '<feed><item><title>text</title></item></feed>'
        r = feedparser._open_resource(s, '', '', '', '', [], {})
        self.assertEqual(s.encode('utf-8'), r.read())
    def test_unicode_1(self):
        s = u'<feed><item><title>text</title></item></feed>'
        r = feedparser._open_resource(s, '', '', '', '', [], {})
        self.assertEqual(s.encode('utf-8'), r.read())
    def test_unicode_2(self):
        s = u'<feed><item><title>t\u00e9xt</title></item></feed>'
        r = feedparser._open_resource(s, '', '', '', '', [], {})
        self.assertEqual(s.encode('utf-8'), r.read())

class TestMakeSafeAbsoluteURI(unittest.TestCase):
    "Exercise the URI joining and sanitization code"
    base = u'http://d.test/d/f.ext'
    def _mktest(rel, expect, doc):
        def fn(self):
            value = feedparser._makeSafeAbsoluteURI(self.base, rel)
            self.assertEqual(value, expect)
        fn.__doc__ = doc
        return fn

    # make the test cases; the call signature is:
    # (relative_url, expected_return_value, test_doc_string)
    test_abs = _mktest(u'https://s.test/', u'https://s.test/', 'absolute uri')
    test_rel = _mktest(u'/new', u'http://d.test/new', 'relative uri')
    test_bad = _mktest(u'x://bad.test/', u'', 'unacceptable uri protocol')
    test_mag = _mktest(u'magnet:?xt=a', u'magnet:?xt=a', 'magnet uri')

    def test_catch_ValueError(self):
        'catch ValueError in Python 2.7 and up'
        uri = u'http://bad]test/'
        value1 = feedparser._makeSafeAbsoluteURI(uri)
        value2 = feedparser._makeSafeAbsoluteURI(self.base, uri)
        swap = feedparser.ACCEPTABLE_URI_SCHEMES
        feedparser.ACCEPTABLE_URI_SCHEMES = ()
        value3 = feedparser._makeSafeAbsoluteURI(self.base, uri)
        feedparser.ACCEPTABLE_URI_SCHEMES = swap
        # Only Python 2.7 and up throw a ValueError, otherwise uri is returned
        self.assertTrue(value1 in (uri, u''))
        self.assertTrue(value2 in (uri, u''))
        self.assertTrue(value3 in (uri, u''))

class TestConvertToIdn(unittest.TestCase):
    "Test IDN support (unavailable in Jython as of Jython 2.5.2)"
    # this is the greek test domain
    hostname = u'\u03c0\u03b1\u03c1\u03ac\u03b4\u03b5\u03b9\u03b3\u03bc\u03b1'
    hostname += u'.\u03b4\u03bf\u03ba\u03b9\u03bc\u03ae'
    def test_control(self):
        r = feedparser._convert_to_idn(u'http://example.test/')
        self.assertEqual(r, u'http://example.test/')
    def test_idn(self):
        r = feedparser._convert_to_idn(u'http://%s/' % (self.hostname,))
        self.assertEqual(r, u'http://xn--hxajbheg2az3al.xn--jxalpdlp/')
    def test_port(self):
        r = feedparser._convert_to_idn(u'http://%s:8080/' % (self.hostname,))
        self.assertEqual(r, u'http://xn--hxajbheg2az3al.xn--jxalpdlp:8080/')

class TestCompression(unittest.TestCase):
    "Test the gzip and deflate support in the HTTP code"
    def test_gzip_good(self):
        f = feedparser.parse('http://localhost:8097/tests/compression/gzip.gz')
        self.assertEqual(f.version, 'atom10')
    def test_gzip_not_compressed(self):
        f = feedparser.parse('http://localhost:8097/tests/compression/gzip-not-compressed.gz')
        self.assertEqual(f.bozo, 1)
        self.assertTrue(isinstance(f.bozo_exception, IOError))
        self.assertEqual(f['feed']['title'], 'gzip')
    def test_gzip_struct_error(self):
        f = feedparser.parse('http://localhost:8097/tests/compression/gzip-struct-error.gz')
        self.assertEqual(f.bozo, 1)
        self.assertTrue(isinstance(f.bozo_exception, struct.error))
    def test_zlib_good(self):
        f = feedparser.parse('http://localhost:8097/tests/compression/deflate.z')
        self.assertEqual(f.version, 'atom10')
    def test_zlib_no_headers(self):
        f = feedparser.parse('http://localhost:8097/tests/compression/deflate-no-headers.z')
        self.assertEqual(f.version, 'atom10')
    def test_zlib_not_compressed(self):
        f = feedparser.parse('http://localhost:8097/tests/compression/deflate-not-compressed.z')
        self.assertEqual(f.bozo, 1)
        self.assertTrue(isinstance(f.bozo_exception, zlib.error))
        self.assertEqual(f['feed']['title'], 'deflate')

class TestHTTPStatus(unittest.TestCase):
    "Test HTTP redirection and other status codes"
    def test_301(self):
        f = feedparser.parse('http://localhost:8097/tests/http/http_status_301.xml')
        self.assertEqual(f.status, 301)
        self.assertEqual(f.href, 'http://localhost:8097/tests/http/target.xml')
        self.assertEqual(f.entries[0].title, 'target')
    def test_302(self):
        f = feedparser.parse('http://localhost:8097/tests/http/http_status_302.xml')
        self.assertEqual(f.status, 302)
        self.assertEqual(f.href, 'http://localhost:8097/tests/http/target.xml')
        self.assertEqual(f.entries[0].title, 'target')
    def test_303(self):
        f = feedparser.parse('http://localhost:8097/tests/http/http_status_303.xml')
        self.assertEqual(f.status, 303)
        self.assertEqual(f.href, 'http://localhost:8097/tests/http/target.xml')
        self.assertEqual(f.entries[0].title, 'target')
    def test_307(self):
        f = feedparser.parse('http://localhost:8097/tests/http/http_status_307.xml')
        self.assertEqual(f.status, 307)
        self.assertEqual(f.href, 'http://localhost:8097/tests/http/target.xml')
        self.assertEqual(f.entries[0].title, 'target')
    def test_304(self):
        # first retrieve the url
        u = 'http://localhost:8097/tests/http/http_status_304.xml'
        f = feedparser.parse(u)
        self.assertEqual(f.status, 200)
        self.assertEqual(f.entries[0].title, 'title 304')
        # extract the etag and last-modified headers
        e = [v for k, v in f.headers.items() if k.lower() == 'etag'][0]
        mh = [v for k, v in f.headers.items() if k.lower() == 'last-modified'][0]
        ms = f.updated
        mt = f.updated_parsed
        md = datetime.datetime(*mt[0:7])
        self.assertTrue(isinstance(mh, basestring))
        self.assertTrue(isinstance(ms, basestring))
        self.assertTrue(isinstance(mt, time.struct_time))
        self.assertTrue(isinstance(md, datetime.datetime))
        # test that sending back the etag results in a 304
        f = feedparser.parse(u, etag=e)
        self.assertEqual(f.status, 304)
        # test that sending back last-modified (string) results in a 304
        f = feedparser.parse(u, modified=ms)
        self.assertEqual(f.status, 304)
        # test that sending back last-modified (9-tuple) results in a 304
        f = feedparser.parse(u, modified=mt)
        self.assertEqual(f.status, 304)
        # test that sending back last-modified (datetime) results in a 304
        f = feedparser.parse(u, modified=md)
        self.assertEqual(f.status, 304)
    def test_404(self):
        f = feedparser.parse('http://localhost:8097/tests/http/http_status_404.xml')
        self.assertEqual(f.status, 404)
    def test_redirect_to_304(self):
        # ensure that an http redirect to an http 304 doesn't
        # trigger a bozo_exception
        u = 'http://localhost:8097/tests/http/http_redirect_to_304.xml'
        f = feedparser.parse(u)
        self.assertTrue(f.bozo == 0)
        self.assertTrue(f.status == 302)

class TestDateParsers(unittest.TestCase):
    "Test the various date parsers; most of the test cases are constructed " \
    "dynamically based on the contents of the `date_tests` dict, below"
    def test_None(self):
        self.assertTrue(feedparser._parse_date(None) is None)
    def _check_date(self, func, dtstring, expected_value):
        try:
            parsed_value = func(dtstring)
        except (OverflowError, ValueError):
            parsed_value = None
        self.assertEqual(parsed_value, expected_value)
        # self.assertEqual(parsed_value, feedparser._parse_date(dtstring))
    def test_year_10000_date(self):
        # On some systems this date string will trigger an OverflowError.
        # On Jython and x64 systems, however, it's interpreted just fine.
        try:
            date = feedparser._parse_date_rfc822(u'Sun, 31 Dec 9999 23:59:59 -9999')
        except OverflowError:
            date = None
        self.assertTrue(date in (None, (10000, 1, 5, 4, 38, 59, 2, 5, 0)))

date_tests = {
    feedparser._parse_date_greek: (
        (u'', None), # empty string
        (u'\u039a\u03c5\u03c1, 11 \u0399\u03bf\u03cd\u03bb 2004 12:00:00 EST', (2004, 7, 11, 17, 0, 0, 6, 193, 0)),
    ),
    feedparser._parse_date_hungarian: (
        (u'', None), # empty string
        (u'2004-j\u00falius-13T9:15-05:00', (2004, 7, 13, 14, 15, 0, 1, 195, 0)),
    ),
    feedparser._parse_date_iso8601: (
        (u'', None), # empty string
        (u'-0312', (2003, 12, 1, 0, 0, 0, 0, 335, 0)), # 2-digit year/month only variant
        (u'031231', (2003, 12, 31, 0, 0, 0, 2, 365, 0)), # 2-digit year/month/day only, no hyphens
        (u'03-12-31', (2003, 12, 31, 0, 0, 0, 2, 365, 0)), # 2-digit year/month/day only
        (u'-03-12', (2003, 12, 1, 0, 0, 0, 0, 335, 0)), # 2-digit year/month only
        (u'03335', (2003, 12, 1, 0, 0, 0, 0, 335, 0)), # 2-digit year/ordinal, no hyphens
        (u'2003-12-31T10:14:55.1234Z', (2003, 12, 31, 10, 14, 55, 2, 365, 0)), # fractional seconds
        # Special case for Google's extra zero in the month
        (u'2003-012-31T10:14:55+00:00', (2003, 12, 31, 10, 14, 55, 2, 365, 0)),
    ),
    feedparser._parse_date_nate: (
        (u'', None), # empty string
        (u'2004-05-25 \uc624\ud6c4 11:23:17', (2004, 5, 25, 14, 23, 17, 1, 146, 0)),
    ),
    feedparser._parse_date_onblog: (
        (u'', None), # empty string
        (u'2004\ub144 05\uc6d4 28\uc77c  01:31:15', (2004, 5, 27, 16, 31, 15, 3, 148, 0)),
    ),
    feedparser._parse_date_perforce: (
        (u'', None), # empty string
        (u'Fri, 2006/09/15 08:19:53 EDT', (2006, 9, 15, 12, 19, 53, 4, 258, 0)),
    ),
    feedparser._parse_date_rfc822: (
        (u'', None), # empty string
        (u'Thu, 01 Jan 0100 00:00:01 +0100', (99, 12, 31, 23, 0, 1, 3, 365, 0)), # ancient date
        (u'Thu, 01 Jan 04 19:48:21 GMT', (2004, 1, 1, 19, 48, 21, 3, 1, 0)), # 2-digit year
        (u'Thu, 01 Jan 2004 19:48:21 GMT', (2004, 1, 1, 19, 48, 21, 3, 1, 0)), # 4-digit year
        (u'Thu,  5 Apr 2012 10:00:00 GMT', (2012, 4, 5, 10, 0, 0, 3, 96, 0)), # 1-digit day
        (u'Wed, 19 Aug 2009 18:28:00 Etc/GMT', (2009, 8, 19, 18, 28, 0, 2, 231, 0)), # etc/gmt timezone
        (u'Wed, 19 Feb 2012 22:40:00 GMT-01:01', (2012, 2, 19, 23, 41, 0, 6, 50, 0)), # gmt+hh:mm timezone
        (u'Mon, 13 Feb, 2012 06:28:00 UTC', (2012, 2, 13, 6, 28, 0, 0, 44, 0)), # extraneous comma
        (u'Thu, 01 Jan 2004 00:00 GMT', (2004, 1, 1, 0, 0, 0, 3, 1, 0)), # no seconds
        (u'Thu, 01 Jan 2004', (2004, 1, 1, 0, 0, 0, 3, 1, 0)), # no time
        # Additional tests to handle Disney's long month names and invalid timezones
        (u'Mon, 26 January 2004 16:31:00 AT', (2004, 1, 26, 20, 31, 0, 0, 26, 0)),
        (u'Mon, 26 January 2004 16:31:00 ET', (2004, 1, 26, 21, 31, 0, 0, 26, 0)),
        (u'Mon, 26 January 2004 16:31:00 CT', (2004, 1, 26, 22, 31, 0, 0, 26, 0)),
        (u'Mon, 26 January 2004 16:31:00 MT', (2004, 1, 26, 23, 31, 0, 0, 26, 0)),
        (u'Mon, 26 January 2004 16:31:00 PT', (2004, 1, 27, 0, 31, 0, 1, 27, 0)),
        # Swapped month and day
        (u'Thu Aug 30 2012 17:26:16 +0200', (2012, 8, 30, 15, 26, 16, 3, 243, 0)),
        (u'Sun, 16 Dec 2012 1:2:3:4 GMT', None), # invalid time
        (u'Sun, 16 zzz 2012 11:47:32 GMT', None), # invalid month
        (u'Sun, Dec x 2012 11:47:32 GMT', None), # invalid day (swapped day/month)
        ('Sun, 16 Dec zz 11:47:32 GMT', None), # invalid year
        ('Sun, 16 Dec 2012 11:47:32 +zz:00', None), # invalid timezone hour
        ('Sun, 16 Dec 2012 11:47:32 +00:zz', None), # invalid timezone minute
        ('Sun, 99 Jun 2009 12:00:00 GMT', None), # out-of-range day
    ),
    feedparser._parse_date_asctime: (
        (u'Sun Jan  4 16:29:06 2004', (2004, 1, 4, 16, 29, 6, 6, 4, 0)),
    ),
    feedparser._parse_date_w3dtf: (
        (u'', None), # empty string
        (u'2003-12-31T10:14:55Z', (2003, 12, 31, 10, 14, 55, 2, 365, 0)), # UTC
        (u'2003-12-31T10:14:55-08:00', (2003, 12, 31, 18, 14, 55, 2, 365, 0)), # San Francisco timezone
        (u'2003-12-31T18:14:55+08:00', (2003, 12, 31, 10, 14, 55, 2, 365, 0)), # Tokyo timezone
        (u'2007-04-23T23:25:47.538+10:00', (2007, 4, 23, 13, 25, 47, 0, 113, 0)), # fractional seconds
        (u'2003-12-31', (2003, 12, 31, 0, 0, 0, 2, 365, 0)), # year/month/day only
        (u'2003-12', (2003, 12, 1, 0, 0, 0, 0, 335, 0)), # year/month only
        (u'2003', (2003, 1, 1, 0, 0, 0, 2, 1, 0)), # year only
        # Special cases for rollovers in leap years
        (u'2004-02-28T18:14:55-08:00', (2004, 2, 29, 2, 14, 55, 6, 60, 0)), # feb 28 in leap year
        (u'2003-02-28T18:14:55-08:00', (2003, 3, 1, 2, 14, 55, 5, 60, 0)), # feb 28 in non-leap year
        (u'2000-02-28T18:14:55-08:00', (2000, 2, 29, 2, 14, 55, 1, 60, 0)), # feb 28 in leap year on century divisible by 400
        # Out-of-range times
        (u'9999-12-31T23:59:59-99:99', None), # Date is out-of-range
        (u'2003-12-31T25:14:55Z', None), # invalid (25 hours)
        (u'2003-12-31T10:61:55Z', None), # invalid (61 minutes)
        (u'2003-12-31T10:14:61Z', None), # invalid (61 seconds)
        # Invalid formats
        (u'22013', None), # Year is too long
        (u'013', None), # Year is too short
        (u'2013-01-27-01', None), # Date has to many parts
        (u'2013-01-28T11:30:00-06:00Textra', None), # Too many 't's
        # Non-integer values
        (u'2013-xx-27', None), # Date
        (u'2013-01-28T09:xx:00Z', None), # Time
        (u'2013-01-28T09:00:00+00:xx', None), # Timezone
        # MSSQL-style dates
        (u'2004-07-08 23:56:58 -00:20', (2004, 7, 9, 0, 16, 58, 4, 191, 0)), # with timezone
        (u'2004-07-08 23:56:58', (2004, 7, 8, 23, 56, 58, 3, 190, 0)), # without timezone
        (u'2004-07-08 23:56:58.0', (2004, 7, 8, 23, 56, 58, 3, 190, 0)), # with fractional second
    )
}

def make_date_test(f, s, t):
    return lambda self: self._check_date(f, s, t)

for func, items in date_tests.iteritems():
    for i, (dtstring, dttuple) in enumerate(items):
        uniqfunc = make_date_test(func, dtstring, dttuple)
        setattr(TestDateParsers, 'test_%s_%02i' % (func.__name__, i), uniqfunc)


class TestHTMLGuessing(unittest.TestCase):
    "Exercise the HTML sniffing code"
    def _mktest(text, expect, doc):
        def fn(self):
            value = bool(feedparser._FeedParserMixin.lookslikehtml(text))
            self.assertEqual(value, expect)
        fn.__doc__ = doc
        return fn

    test_text_1 = _mktest(u'plain text', False, u'plain text')
    test_text_2 = _mktest(u'2 < 3', False, u'plain text with angle bracket')
    test_html_1 = _mktest(u'<a href="">a</a>', True, u'anchor tag')
    test_html_2 = _mktest(u'<i>i</i>', True, u'italics tag')
    test_html_3 = _mktest(u'<b>b</b>', True, u'bold tag')
    test_html_4 = _mktest(u'<code>', False, u'allowed tag, no end tag')
    test_html_5 = _mktest(u'<rss> .. </rss>', False, u'disallowed tag')
    test_entity_1 = _mktest(u'AT&T', False, u'corporation name')
    test_entity_2 = _mktest(u'&copy;', True, u'named entity reference')
    test_entity_3 = _mktest(u'&#169;', True, u'numeric entity reference')
    test_entity_4 = _mktest(u'&#xA9;', True, u'hex numeric entity reference')

#---------- additional api unit tests, not backed by files

class TestBuildRequest(unittest.TestCase):
    "Test that HTTP request objects are created as expected"
    def test_extra_headers(self):
        """You can pass in extra headers and they go into the request object."""

        request = feedparser._build_urllib2_request(
          'http://example.com/feed',
          'agent-name',
          None, None, None, None,
          {'Cache-Control': 'max-age=0'})
        # nb, urllib2 folds the case of the headers
        self.assertEqual(
          request.get_header('Cache-control'), 'max-age=0')


class TestLxmlBug(unittest.TestCase):
    def test_lxml_etree_bug(self):
        try:
            import lxml.etree
        except ImportError:
            pass
        else:
            doc = u"<feed>&illformed_charref</feed>".encode('utf8')
            # Importing lxml.etree currently causes libxml2 to
            # throw SAXException instead of SAXParseException.
            feedparser.parse(feedparser._StringIO(doc))
        self.assertTrue(True)

#---------- parse test files and create test methods ----------
def convert_to_utf8(data):
    "Identify data's encoding using its byte order mark" \
    "and convert it to its utf-8 equivalent"
    if data[:4] == _l2bytes([0x4c, 0x6f, 0xa7, 0x94]):
        return data.decode('cp037').encode('utf-8')
    elif data[:4] == _l2bytes([0x00, 0x00, 0xfe, 0xff]):
        if not _UTF32_AVAILABLE:
            return None
        return data.decode('utf-32be').encode('utf-8')
    elif data[:4] == _l2bytes([0xff, 0xfe, 0x00, 0x00]):
        if not _UTF32_AVAILABLE:
            return None
        return data.decode('utf-32le').encode('utf-8')
    elif data[:4] == _l2bytes([0x00, 0x00, 0x00, 0x3c]):
        if not _UTF32_AVAILABLE:
            return None
        return data.decode('utf-32be').encode('utf-8')
    elif data[:4] == _l2bytes([0x3c, 0x00, 0x00, 0x00]):
        if not _UTF32_AVAILABLE:
            return None
        return data.decode('utf-32le').encode('utf-8')
    elif data[:4] == _l2bytes([0x00, 0x3c, 0x00, 0x3f]):
        return data.decode('utf-16be').encode('utf-8')
    elif data[:4] == _l2bytes([0x3c, 0x00, 0x3f, 0x00]):
        return data.decode('utf-16le').encode('utf-8')
    elif (data[:2] == _l2bytes([0xfe, 0xff])) and (data[2:4] != _l2bytes([0x00, 0x00])):
        return data[2:].decode('utf-16be').encode('utf-8')
    elif (data[:2] == _l2bytes([0xff, 0xfe])) and (data[2:4] != _l2bytes([0x00, 0x00])):
        return data[2:].decode('utf-16le').encode('utf-8')
    elif data[:3] == _l2bytes([0xef, 0xbb, 0xbf]):
        return data[3:]
    # no byte order mark was found
    return data

skip_re = re.compile(_s2bytes("SkipUnless:\s*(.*?)\n"))
desc_re = re.compile(_s2bytes("Description:\s*(.*?)\s*Expect:\s*(.*)\s*-->"))
def getDescription(xmlfile, data):
    """Extract test data

    Each test case is an XML file which contains not only a test feed
    but also the description of the test and the condition that we
    would expect the parser to create when it parses the feed.  Example:
    <!--
    Description: feed title
    Expect:      feed['title'] == u'Example feed'
    -->
    """
    skip_results = skip_re.search(data)
    if skip_results:
        skipUnless = skip_results.group(1).strip()
    else:
        skipUnless = '1'
    search_results = desc_re.search(data)
    if not search_results:
        raise RuntimeError, "can't parse %s" % xmlfile
    description, evalString = map(lambda s: s.strip(), list(search_results.groups()))
    description = xmlfile + ": " + unicode(description, 'utf8')
    return description, evalString, skipUnless

def buildTestCase(xmlfile, description, evalString):
    func = lambda self, xmlfile=xmlfile, evalString=evalString: \
         self.failUnlessEval(xmlfile, evalString)
    func.__doc__ = description
    return func

def runtests():
    "Read the files in the tests/ directory, dynamically add tests to the " \
    "TestCases above, spawn the HTTP server, and run the test suite"
    if sys.argv[1:]:
        allfiles = filter(lambda s: s.endswith('.xml'), reduce(operator.add, map(glob.glob, sys.argv[1:]), []))
        wellformedfiles = illformedfiles = encodingfiles = entitiesfiles = microformatfiles = []
        sys.argv = [sys.argv[0]] #+ sys.argv[2:]
    else:
        allfiles = glob.glob(os.path.join('.', 'tests', '**', '**', '*.xml'))
        wellformedfiles = glob.glob(os.path.join('.', 'tests', 'wellformed', '**', '*.xml'))
        illformedfiles = glob.glob(os.path.join('.', 'tests', 'illformed', '*.xml'))
        encodingfiles = glob.glob(os.path.join('.', 'tests', 'encoding', '*.xml'))
        entitiesfiles = glob.glob(os.path.join('.', 'tests', 'entities', '*.xml'))
        microformatfiles = glob.glob(os.path.join('.', 'tests', 'microformats', '**', '*.xml'))
    httpd = None
    # there are several compression test cases that must be accounted for
    # as well as a number of http status tests that redirect to a target
    # and a few `_open_resource`-related tests
    httpcount = 6 + 16 + 2
    httpcount += len([f for f in allfiles if 'http' in f])
    httpcount += len([f for f in wellformedfiles if 'http' in f])
    httpcount += len([f for f in illformedfiles if 'http' in f])
    httpcount += len([f for f in encodingfiles if 'http' in f])
    try:
        for c, xmlfile in enumerate(allfiles + encodingfiles + illformedfiles + entitiesfiles):
            addTo = TestCase
            if xmlfile in encodingfiles:
                addTo = TestEncodings
            elif xmlfile in entitiesfiles:
                addTo = (TestStrictParser, TestLooseParser)
            elif xmlfile in microformatfiles:
                addTo = TestMicroformats
            elif xmlfile in wellformedfiles:
                addTo = (TestStrictParser, TestLooseParser)
            f = open(xmlfile, 'rb')
            data = f.read()
            f.close()
            if 'encoding' in xmlfile:
                data = convert_to_utf8(data)
                if data is None:
                    # convert_to_utf8 found a byte order mark for utf_32
                    # but it's not supported in this installation of Python
                    if 'http' in xmlfile:
                        httpcount -= 1 + (xmlfile in wellformedfiles)
                    continue
            description, evalString, skipUnless = getDescription(xmlfile, data)
            testName = 'test_%06d' % c
            ishttp = 'http' in xmlfile
            try:
                if not eval(skipUnless): raise NotImplementedError
            except (ImportError, LookupError, NotImplementedError, AttributeError):
                if ishttp:
                    httpcount -= 1 + (xmlfile in wellformedfiles)
                continue
            if ishttp:
                xmlfile = 'http://%s:%s/%s' % (_HOST, _PORT, posixpath.normpath(xmlfile.replace('\\', '/')))
            testFunc = buildTestCase(xmlfile, description, evalString)
            if isinstance(addTo, tuple):
                setattr(addTo[0], testName, testFunc)
                setattr(addTo[1], testName, testFunc)
            else:
                setattr(addTo, testName, testFunc)
        if httpcount:
            httpd = FeedParserTestServer(httpcount)
            httpd.daemon = True
            httpd.start()
            httpd.ready.wait()
        testsuite = unittest.TestSuite()
        testloader = unittest.TestLoader()
        testsuite.addTest(testloader.loadTestsFromTestCase(TestCase))
        testsuite.addTest(testloader.loadTestsFromTestCase(TestStrictParser))
        testsuite.addTest(testloader.loadTestsFromTestCase(TestLooseParser))
        testsuite.addTest(testloader.loadTestsFromTestCase(TestEncodings))
        testsuite.addTest(testloader.loadTestsFromTestCase(TestDateParsers))
        testsuite.addTest(testloader.loadTestsFromTestCase(TestHTMLGuessing))
        testsuite.addTest(testloader.loadTestsFromTestCase(TestHTTPStatus))
        testsuite.addTest(testloader.loadTestsFromTestCase(TestCompression))
        testsuite.addTest(testloader.loadTestsFromTestCase(TestConvertToIdn))
        testsuite.addTest(testloader.loadTestsFromTestCase(TestMicroformats))
        testsuite.addTest(testloader.loadTestsFromTestCase(TestOpenResource))
        testsuite.addTest(testloader.loadTestsFromTestCase(TestFeedParserDict))
        testsuite.addTest(testloader.loadTestsFromTestCase(TestMakeSafeAbsoluteURI))
        testsuite.addTest(testloader.loadTestsFromTestCase(TestEverythingIsUnicode))
        testsuite.addTest(testloader.loadTestsFromTestCase(TestTemporaryFallbackBehavior))
        testsuite.addTest(testloader.loadTestsFromTestCase(TestLxmlBug))
        testresults = unittest.TextTestRunner(verbosity=1).run(testsuite)

        # Return 0 if successful, 1 if there was a failure
        sys.exit(not testresults.wasSuccessful())
    finally:
        if httpd:
            if httpd.requests:
                # Should never get here unless something went horribly wrong, like the
                # user hitting Ctrl-C.  Tell our HTTP server that it's done, then do
                # one more request to flush it.  This rarely works; the combination of
                # threading, self-terminating HTTP servers, and unittest is really
                # quite flaky.  Just what you want in a testing framework, no?
                httpd.requests = 0
                if httpd.ready:
                    urllib.urlopen('http://127.0.0.1:8097/tests/wellformed/rss/aaa_wellformed.xml').read()
            httpd.join(0)

if __name__ == "__main__":
    runtests()
