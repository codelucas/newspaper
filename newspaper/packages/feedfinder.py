"""feedfinder: Find the Web feed for a Web page
http://www.aaronsw.com/2002/feedfinder/

Usage:
  feed(uri) - returns feed found for a URI
  feeds(uri) - returns all feeds found for a URI

    >>> import feedfinder
    >>> feedfinder.feed('scripting.com')
    'http://scripting.com/rss.xml'
    >>>
    >>> feedfinder.feeds('scripting.com')
    ['http://delong.typepad.com/sdj/atom.xml',
     'http://delong.typepad.com/sdj/index.rdf',
     'http://delong.typepad.com/sdj/rss.xml']
    >>>

Can also use from the command line.  Feeds are returned one per line:

    $ python feedfinder.py diveintomark.org
    http://diveintomark.org/xml/atom.xml

How it works:
  0. At every step, feeds are minimally verified to make sure they are really feeds.
  1. If the URI points to a feed, it is simply returned; otherwise
     the page is downloaded and the real fun begins.
  2. Feeds pointed to by LINK tags in the header of the page (autodiscovery)
  3. <A> links to feeds on the same server ending in ".rss", ".rdf", ".xml", or
     ".atom"
  4. <A> links to feeds on the same server containing "rss", "rdf", "xml", or "atom"
  5. <A> links to feeds on external servers ending in ".rss", ".rdf", ".xml", or
     ".atom"
  6. <A> links to feeds on external servers containing "rss", "rdf", "xml", or "atom"
  7. Try some guesses about common places for feeds (index.xml, atom.xml, etc.).
  8. As a last ditch effort, we search Syndic8 for feeds matching the URI
"""

__version__ = "1.371"
__date__ = "2006-04-24"
__maintainer__ = "Aaron Swartz (me@aaronsw.com)"
__author__ = "Mark Pilgrim (http://diveintomark.org)"
__copyright__ = "Copyright 2002-4, Mark Pilgrim; 2006 Aaron Swartz"
__license__ = "Python"
__credits__ = """Abe Fettig for a patch to sort Syndic8 feeds by popularity
Also Jason Diamond, Brian Lalor for bug reporting and patches"""

_debug = 0

import sgmllib
import urllib
import urlparse
import re
import sys
import robotparser
import threading

class TimeoutError(Exception):
    pass

def timelimit(timeout):
    """borrowed from web.py"""
    def _1(function):
        def _2(*args, **kw):
            class Dispatch(threading.Thread):
                def __init__(self):
                    threading.Thread.__init__(self)
                    self.result = None
                    self.error = None

                    self.setDaemon(True)
                    self.start()

                def run(self):
                    try:
                        self.result = function(*args, **kw)
                    except:
                        self.error = sys.exc_info()

            c = Dispatch()
            c.join(timeout)
            if c.isAlive():
                raise TimeoutError, 'took too long'
            if c.error:
                raise c.error[0], c.error[1]
            return c.result
        return _2
    return _1

# XML-RPC support allows feedfinder to query Syndic8 for possible matches.
# Python 2.3 now comes with this module by default, otherwise you can download it
try:
    import xmlrpclib # http://www.pythonware.com/products/xmlrpc/
except ImportError:
    xmlrpclib = None

if not dict:
    def dict(aList):
        rc = {}
        for k, v in aList:
            rc[k] = v
        return rc

def _debuglog(message):
    if _debug: print message

class URLGatekeeper:
    """a class to track robots.txt rules across multiple servers"""
    def __init__(self):
        self.rpcache = {} # a dictionary of RobotFileParser objects, by domain
        self.urlopener = urllib.FancyURLopener()
        self.urlopener.version = "feedfinder/" + __version__ + " " + self.urlopener.version + " +http://www.aaronsw.com/2002/feedfinder/"
        _debuglog(self.urlopener.version)
        self.urlopener.addheaders = [('User-agent', self.urlopener.version)]
        robotparser.URLopener.version = self.urlopener.version
        robotparser.URLopener.addheaders = self.urlopener.addheaders

    def _getrp(self, url):
        protocol, domain = urlparse.urlparse(url)[:2]
        if self.rpcache.has_key(domain):
            return self.rpcache[domain]
        baseurl = '%s://%s' % (protocol, domain)
        robotsurl = urlparse.urljoin(baseurl, 'robots.txt')
        _debuglog('fetching %s' % robotsurl)
        rp = robotparser.RobotFileParser(robotsurl)
        try:
            rp.read()
        except:
            pass
        self.rpcache[domain] = rp
        return rp

    def can_fetch(self, url):
        rp = self._getrp(url)
        allow = rp.can_fetch(self.urlopener.version, url)
        _debuglog("gatekeeper of %s says %s" % (url, allow))
        return allow

    @timelimit(10)
    def get(self, url, check=True):
        if check and not self.can_fetch(url): return ''
        try:
            return self.urlopener.open(url).read()
        except:
            return ''

_gatekeeper = URLGatekeeper()

class BaseParser(sgmllib.SGMLParser):
    def __init__(self, baseuri):
        sgmllib.SGMLParser.__init__(self)
        self.links = []
        self.baseuri = baseuri

    def normalize_attrs(self, attrs):
        def cleanattr(v):
            v = sgmllib.charref.sub(lambda m: unichr(int(m.groups()[0])), v)
            v = v.strip()
            v = v.replace('&lt;', '<').replace('&gt;', '>').replace('&apos;', "'").replace('&quot;', '"').replace('&amp;', '&')
            return v
        attrs = [(k.lower(), cleanattr(v)) for k, v in attrs]
        attrs = [(k, k in ('rel','type') and v.lower() or v) for k, v in attrs]
        return attrs

    def do_base(self, attrs):
        attrsD = dict(self.normalize_attrs(attrs))
        if not attrsD.has_key('href'): return
        self.baseuri = attrsD['href']

    def error(self, *a, **kw): pass # we're not picky

class LinkParser(BaseParser):
    FEED_TYPES = ('application/rss+xml',
                  'text/xml',
                  'application/atom+xml',
                  'application/x.atom+xml',
                  'application/x-atom+xml')
    def do_link(self, attrs):
        attrsD = dict(self.normalize_attrs(attrs))
        if not attrsD.has_key('rel'): return
        rels = attrsD['rel'].split()
        if 'alternate' not in rels: return
        if attrsD.get('type') not in self.FEED_TYPES: return
        if not attrsD.has_key('href'): return
        self.links.append(urlparse.urljoin(self.baseuri, attrsD['href']))

class ALinkParser(BaseParser):
    def start_a(self, attrs):
        attrsD = dict(self.normalize_attrs(attrs))
        if not attrsD.has_key('href'): return
        self.links.append(urlparse.urljoin(self.baseuri, attrsD['href']))

def makeFullURI(uri):
    uri = uri.strip()
    if uri.startswith('feed://'):
        uri = 'http://' + uri.split('feed://', 1).pop()
    for x in ['http', 'https']:
        if uri.startswith('%s://' % x):
            return uri
    return 'http://%s' % uri

def getLinks(data, baseuri):
    p = LinkParser(baseuri)
    p.feed(data)
    return p.links

def getALinks(data, baseuri):
    p = ALinkParser(baseuri)
    p.feed(data)
    return p.links

def getLocalLinks(links, baseuri):
    baseuri = baseuri.lower()
    urilen = len(baseuri)
    return [l for l in links if l.lower().startswith(baseuri)]

def isFeedLink(link):
    return link[-4:].lower() in ('.rss', '.rdf', '.xml', '.atom')

def isXMLRelatedLink(link):
    link = link.lower()
    return link.count('rss') + link.count('rdf') + link.count('xml') + link.count('atom')

r_brokenRedirect = re.compile('<newLocation[^>]*>(.*?)</newLocation>', re.S)
def tryBrokenRedirect(data):
    if '<newLocation' in data:
        newuris = r_brokenRedirect.findall(data)
        if newuris: return newuris[0].strip()

def couldBeFeedData(data):
    data = data.lower()
    if data.count('<html'): return 0
    return data.count('<rss') + data.count('<rdf') + data.count('<feed')

def isFeed(uri):
    _debuglog('seeing if %s is a feed' % uri)
    protocol = urlparse.urlparse(uri)
    if protocol[0] not in ('http', 'https'): return 0
    data = _gatekeeper.get(uri)
    return couldBeFeedData(data)

def sortFeeds(feed1Info, feed2Info):
    return cmp(feed2Info['headlines_rank'], feed1Info['headlines_rank'])

def getFeedsFromSyndic8(uri):
    feeds = []
    try:
        server = xmlrpclib.Server('http://www.syndic8.com/xmlrpc.php')
        feedids = server.syndic8.FindFeeds(uri)
        infolist = server.syndic8.GetFeedInfo(feedids, ['headlines_rank','status','dataurl'])
        infolist.sort(sortFeeds)
        feeds = [f['dataurl'] for f in infolist if f['status']=='Syndicated']
        _debuglog('found %s feeds through Syndic8' % len(feeds))
    except:
        pass
    return feeds

def feeds(uri, all=False, querySyndic8=False, _recurs=None):
    if _recurs is None: _recurs = [uri]
    fulluri = makeFullURI(uri)
    try:
        data = _gatekeeper.get(fulluri, check=False)
    except:
        return []
    # is this already a feed?
    if couldBeFeedData(data):
        return [fulluri]
    newuri = tryBrokenRedirect(data)
    if newuri and newuri not in _recurs:
        _recurs.append(newuri)
        return feeds(newuri, all=all, querySyndic8=querySyndic8, _recurs=_recurs)
    # nope, it's a page, try LINK tags first
    _debuglog('looking for LINK tags')
    try:
        outfeeds = getLinks(data, fulluri)
    except:
        outfeeds = []
    _debuglog('found %s feeds through LINK tags' % len(outfeeds))
    outfeeds = filter(isFeed, outfeeds)
    if all or not outfeeds:
        # no LINK tags, look for regular <A> links that point to feeds
        _debuglog('no LINK tags, looking at A tags')
        try:
            links = getALinks(data, fulluri)
        except:
            links = []
        locallinks = getLocalLinks(links, fulluri)
        # look for obvious feed links on the same server
        outfeeds.extend(filter(isFeed, filter(isFeedLink, locallinks)))
        if all or not outfeeds:
            # look harder for feed links on the same server
            outfeeds.extend(filter(isFeed, filter(isXMLRelatedLink, locallinks)))
        if all or not outfeeds:
            # look for obvious feed links on another server
            outfeeds.extend(filter(isFeed, filter(isFeedLink, links)))
        if all or not outfeeds:
            # look harder for feed links on another server
            outfeeds.extend(filter(isFeed, filter(isXMLRelatedLink, links)))
    if all or not outfeeds:
        _debuglog('no A tags, guessing')
        suffixes = [ # filenames used by popular software:
          'atom.xml', # blogger, TypePad
          'index.atom', # MT, apparently
          'index.rdf', # MT
          'rss.xml', # Dave Winer/Manila
          'index.xml', # MT
          'index.rss' # Slash
        ]
        outfeeds.extend(filter(isFeed, [urlparse.urljoin(fulluri, x) for x in suffixes]))
    if (all or not outfeeds) and querySyndic8:
        # still no luck, search Syndic8 for feeds (requires xmlrpclib)
        _debuglog('still no luck, searching Syndic8')
        outfeeds.extend(getFeedsFromSyndic8(uri))
    if hasattr(__builtins__, 'set') or __builtins__.has_key('set'):
        outfeeds = list(set(outfeeds))
    return outfeeds

getFeeds = feeds # backwards-compatibility

def feed(uri):
    #todo: give preference to certain feed formats
    feedlist = feeds(uri)
    if feedlist:
        return feedlist[0]
    else:
        return None

##### test harness ######

def test():
    uri = 'http://cnn.com'
    failed = []
    count = 0
    while 1:
        data = _gatekeeper.get(uri)
        if data.find('Atom autodiscovery test') == -1: break
        sys.stdout.write('.')
        sys.stdout.flush()
        count += 1
        links = getLinks(data, uri)
        if not links:
            print '\n*** FAILED ***', uri, 'could not find link'
            failed.append(uri)
        elif len(links) > 1:
            print '\n*** FAILED ***', uri, 'found too many links'
            failed.append(uri)
        else:
            atomdata = urllib.urlopen(links[0]).read()
            if atomdata.find('<link rel="alternate"') == -1:
                print '\n*** FAILED ***', uri, 'retrieved something that is not a feed'
                failed.append(uri)
            else:
                backlink = atomdata.split('href="').pop().split('"')[0]
                if backlink != uri:
                    print '\n*** FAILED ***', uri, 'retrieved wrong feed'
                    failed.append(uri)
        if data.find('<link rel="next" href="') == -1: break
        uri = urlparse.urljoin(uri, data.split('<link rel="next" href="').pop().split('"')[0])
    print
    print count, 'tests executed,', len(failed), 'failed'

if __name__ == '__main__':
    args = sys.argv[1:]
    if args and args[0] == '--debug':
        _debug = 1
        args.pop(0)
    if args:
        uri = args[0]
    else:
        uri = 'http://diveintomark.org/'
    if uri == 'test':
        test()
    else:
        print "\n".join(getFeeds(uri))