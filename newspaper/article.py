# -*- coding: utf-8 -*-

from .utils import fix_unicode

class Article(object):

    def __init__(self, href, title=u'', source_url=None, from_feed=False):
        """imgs is a list of image src urls so our image
        Scraper does not have to re-download every image
        is_media_news() = gallery, video vs. a lot of text

        top_img is the "best img" of an article, the one we
        send to Wintria.

        keywords are stored as a delimited string.
        s3_status is 0 if an img failed to upload to s3,
        1 if it worked.

        lxml_root tries to use the html parser first from lxml.
        if that fails, we attempt again with the slow but sure
        BeautifulSoup parser

        authors is a list of two word names.

        published is the date in a string format of the
        publishing date

        """

        if source_url is None:
            source_url = urlparse(href).netloc

        if source_url is None or source_url == '':
            self.rejected = True
            return

        href = fix_unicode(href)
        title = fix_unicode(title)
        source_url = fix_unicode(source_url)

        href = prepare_url(href, source_url)


        self.href = href
        self.title = title
        self.top_img = u''
        self.text = u''
        self.keywords = u''
        self.s3_status = 0
        self.authors = []
        self.published = u''

        # below are auxiliary fields, not sent to server

        self.domain = urlparse(source_url).netloc
        self.scheme = urlparse(source_url).scheme
        self.score = 0
        self.rejected = False
        self.from_feed = from_feed

        self.html = u''
        self.lxml_root = None

        self.imgs = []

        # Verify the Link's url on creation, this is
        # our biggest hint and least resource intensive
        if not from_feed:
            self.verify_url()


    def url_to_key(self, url):
        """returns a md5 rep of the url, we use
        this hash key in our amzn s3 urls"""
        return base64.urlsafe_b64encode(
                hashlib.md5(url).digest())


    def download(self):
        """downloads the link's html content"""

        try:
            req_kwargs = {
                'headers' : {'User-Agent': useragent()},
                'cookies' : cj(),
                'timeout' : 7,
                'allow_redirects' : True
            }
            self.html = requests.get(url=self.href,
                                     **req_kwargs).text

            if self.html is None:
                self.html = u''
                return

        except Exception, e:
            self.rejected = True
            logger.error('%s on %s' % (e, self.href))


    def parse(self):
        """extracts the lxml root, if lxml fails
        we also extract the BeautifulSoup root"""

        @timelimit(2)
        def lxml_wrapper(html):
            return lxml.html.fromstring(html)

        @timelimit(4)
        def soup_wrapper(html):
            return lxml.html.soupparser.\
                        fromstring(html)

        try:
            self.lxml_root = lxml_wrapper(self.html)

        except:
            try:
                self.lxml_root = soup_wrapper(self.html)

            except TimeoutError:
                logger.error('link lxml parse failed timed out')
                self.rejected = True

            except Exception, e:
                logger.error('link lxml parse failed %s' % e)
                self.rejected = True


    def annotate(self):
        """public annotate, g2 is a slow but sure backup"""
        g = Goose()
        g2 = Goose({'parser_class':'soup'})

        try:
            self._annotate(g)

        except TimeoutError:
            self._annotate(g2)
            logger.debug('custom link annotate '
                         'caught with lxml soup parser')


    @timelimit(6)
    def _annotate(self, g):
        """custom internal annotation mechanism"""

        obj = g.extract(raw_html=self.html)
        self.set_text(obj.cleaned_text)
        self.set_keywords(obj.meta_keywords.split(','))
        self.set_title(obj.title)


    def upload_img(self):
        """prior to this method call, we already have
        downloaded candidates for the 'top img' and all src
        imgs on the html page. Send these links into a custom
        img scrapper class for size, entropy analysis,
        return top image"""

        s = Scraper(url=self.href, imgs=self.imgs,
                    top_img=self.top_img)
        pth = ''

        try:
            img, img_url = s.thumbnail()
            file_key = self.url_to_key(self.href)

            local = file_key + '.jpg'
            pth = os.path.join(TOPDIR, local)

            if img is None:
                raise Exception
            try:
                img.save(pth)
            except IOError:
                img.convert('RGB').save(pth)

        except:
            self.top_img = None
            try:
                os.remove(pth)
            except:
                pass
            return False

        successful = s3.upload_img(pth, file_key)

        self.top_img = img_url

        try:
            os.remove(pth)
            if successful:
                self.s3_status = 1
                return True
        except:
            return False


    def verify_url(self):
        """performs a check on the url of this link to
        determine if a real news article or not"""
        if self.rejected:
            return
        self.rejected = not is_valid_url(self.href)


    def verify_body(self):
        """if the article's body text is long enough
        to meet standard article requirements, we keep
        the article"""
        if self.rejected:
            return
        self.rejected = not is_valid_body(self)


    def is_media_news(self):
        """if the article is a gallery, video, etc related"""

        safe_urls = [
            '/video', '/slide', '/gallery',
            '/powerpoint', '/fashion', '/glamour',
            '/cloth'
        ]

        for s in safe_urls:
            if s in self.href:
                return True

        return False


    def prepare_keys(self):
        """keyword extraction wrapper"""
        keys = get_keyphrases(self)
        self.set_keywords(keys)


    def set_images(self):
        """wrapper for setting images via the fast
        lxml or the slow BS if lxml fails"""

        if self.lxml_root:
            img = lxml_top_img(self.lxml_root)
            self.top_img = fix_unicode(img)
            t_imgs = lxml_imgs(self, self.lxml_root)
            t_imgs = [ fix_unicode(t) for t in t_imgs ]
            self.imgs = t_imgs

        else:
            pass
            # logger.debug('top img extract failed')


    def set_title(self, title):
        """titles are length limited"""
        title = fix_unicode(title)[:MAX_TITLE]
        if title:
            self.title = title


    def set_text(self, text):
        """text is length limited"""
        text = fix_unicode(text)[:MAX_TEXT-5]
        if text:
            self.text = text


    def set_keywords(self, keywords):
        """keys are stored in list format"""
        if not isinstance(keywords, list):
            raise Exception("Keyw input must be list!")

        if keywords:

            keywords = [ fix_unicode(k) for k in
                         keywords[:MAX_KEYWORDS] ]

            str_keys = KEYW_DELIM.join(keywords)

            if str_keys:
                self.keywords = str_keys

    def get_proper_keys(self):
        """in list form"""
        if self.keywords:
            return self.keywords.split(KEYW_DELIM)
        return None
