# -*- coding: utf-8 -*-

"""
"""

import re
import copy
import urlparse

from .packages.tldextract import tldextract
from .utils import (
    StringSplitter, StringReplacement, ReplaceSequence)
from .urls import (
    get_path, get_domain, get_scheme, prepare_url)


MOTLEY_REPLACEMENT = StringReplacement("&#65533;", "")
ESCAPED_FRAGMENT_REPLACEMENT = StringReplacement(u"#!", u"?_escaped_fragment_=")
TITLE_REPLACEMENTS = ReplaceSequence().create(u"&raquo;").append(u"»")
PIPE_SPLITTER = StringSplitter("\\|")
DASH_SPLITTER = StringSplitter(" - ")
ARROWS_SPLITTER = StringSplitter("»")
COLON_SPLITTER = StringSplitter(":")
SPACE_SPLITTER = StringSplitter(' ')
NO_STRINGS = set()
A_REL_TAG_SELECTOR = "a[rel=tag]"
A_HREF_TAG_SELECTOR = "a[href*='/tag/'], a[href*='/tags/'], a[href*='/topic/'], a[href*='?keyword=']"
RE_LANG = r'^[A-Za-z]{2}$'

good_paths = ['story', 'article', 'feature', 'featured', 'slides',
              'slideshow', 'gallery', 'news', 'video', 'media',
              'v', 'radio', 'press']
bad_chunks = ['careers', 'contact', 'about', 'faq', 'terms', 'privacy',
              'advert', 'preferences', 'feedback', 'info', 'browse', 'howto',
              'account', 'subscribe', 'donate', 'shop', 'admin']
bad_domains = ['amazon', 'doubleclick', 'twitter']


class ContentExtractor(object):

    def __init__(self, config):
        self.config = config
        self.parser = self.config.get_parser()
        self.language = config.language
        self.stopwords_class = config.stopwords_class

    def get_language(self, article):
        """
        Returns the language is by the article or
        the configuration language.
        """
        if self.config.use_meta_language == True:
            if article.meta_lang:
                return article.meta_lang
        return self.config.language

    def get_authors(self, article):
        """
        Fetch the authors of the article, return as a list
        Only works for english articles.
        """
        _digits = re.compile('\d')
        def contains_digits(d):
            return bool(_digits.search(d))

        def parse_byline(search_str):
            """
            Takes a candidate line of html or text and
            extracts out the name(s) in list form
            >>> search_str('<div>By: <strong>Lucas Ou-Yang</strong>, \
                            <strong>Alex Smith</strong></div>')
            ['Lucas Ou-Yang', 'Alex Smith']
            """
            # Remove HTML boilerplate
            search_str = re.sub('<[^<]+?>', '', search_str)

            # Remove original By statement
            search_str = re.sub('[bB][yY][\:\s]|[fF]rom[\:\s]', '', search_str)

            search_str = search_str.strip()

            # Chunk the line by non alphanumeric tokens (few name exceptions)

            # >>> re.split("[^\w\'\-]", "Lucas Ou-Yang, Dean O'Brian and Ronald")
            # ['Lucas Ou-Yang', '', 'Dean O'Brian', 'and', 'Ronald']

            name_tokens = re.split("[^\w\'\-]", search_str)
            name_tokens = [s.strip() for s in name_tokens]

            _authors = []
            curname = [] # List of first, last name tokens
            DELIM = ['and', '']

            for token in name_tokens:
                if token in DELIM:
                    # should we allow middle names?
                    valid_name = (len(curname) == 2)
                    if valid_name:
                        _authors.append(' '.join(curname))
                        curname = []

                elif not contains_digits(token):
                    curname.append(token)

            # One last check at end
            valid_name = (len(curname) >= 2)
            if valid_name:
                _authors.append(' '.join(curname))

            return _authors

        # Try 1: Search popular author tags for authors

        ATTRS = ['name', 'rel', 'itemprop', 'class', 'id']
        VALS = ['author', 'byline']
        matches = []
        _authors, authors = [], []
        doc = article.doc
        html = article.html

        for attr in ATTRS:
            for val in VALS:
                # found = doc.xpath('//*[@%s="%s"]' % (attr, val))
                found = self.parser.getElementsByTag(doc, attr=attr, value=val)
                matches.extend(found)

        for match in matches:
            content = u''

            if match.tag == 'meta':
                mm = match.xpath('@content')
                if len(mm) > 0:
                    content = mm[0]

            else: # match.tag == <any other tag>
                content = match.text or u'' # text_content()

            if len(content) > 0:
                _authors.extend(parse_byline(content))

        uniq = list(set([s.lower() for s in _authors]))

        for name in uniq:
            names = [w.capitalize() for w in name.split(' ')]
            authors.append(' '.join(names))

        return authors or []

        # TODO Method 2: Search raw html for a by-line

        # match = re.search('By[\: ].*\\n|From[\: ].*\\n', html)

        # try:
        #    # Don't let zone be too long
        #    line = match.group(0)[:100]
        #    authors = parse_byline(line)
        # except:
        #    return [] # Failed to find anything

        # return authors

    def get_title(self, article):
        """
        Fetch the article title and analyze it.
        """
        title = ''
        doc = article.doc

        title_element = self.parser.getElementsByTag(doc, tag='title')
        # no title found
        if title_element is None or len(title_element) == 0:
            return title

        # title elem found
        title_text = self.parser.getText(title_element[0])
        used_delimeter = False

        # split title with |
        if '|' in title_text:
            title_text = self.split_title(title_text, PIPE_SPLITTER)
            used_delimeter = True

        # split title with -
        if not used_delimeter and '-' in title_text:
            title_text = self.split_title(title_text, DASH_SPLITTER)
            used_delimeter = True

        # split title with »
        if not used_delimeter and u'»' in title_text:
            title_text = self.split_title(title_text, ARROWS_SPLITTER)
            used_delimeter = True

        # split title with :
        if not used_delimeter and ':' in title_text:
            title_text = self.split_title(title_text, COLON_SPLITTER)
            used_delimeter = True

        title = MOTLEY_REPLACEMENT.replaceAll(title_text)
        return title

    def split_title(self, title, splitter):
        """
        Split the title to best part possible.
        """
        large_text_length = 0
        large_text_index = 0
        title_pieces = splitter.split(title)

        # find the largest title piece
        for i in range(len(title_pieces)):
            current = title_pieces[i]
            if len(current) > large_text_length:
                large_text_length = len(current)
                large_text_index = i

        # replace content
        title = title_pieces[large_text_index]
        return TITLE_REPLACEMENTS.replaceAll(title).strip()

    def get_favicon(self, article):
        """
        Extract the favicon from a website
        http://en.wikipedia.org/wiki/Favicon
        <link rel="shortcut icon" type="image/png" href="favicon.png" />
        <link rel="icon" type="image/png" href="favicon.png" />
        """
        kwargs = {'tag': 'link', 'attr': 'rel', 'value': 'icon'}
        meta = self.parser.getElementsByTag(article.doc, **kwargs)
        if meta:
            favicon = self.parser.getAttribute(meta[0], 'href')
            return favicon
        return ''

    def get_meta_lang(self, article):
        """
        Extract content language from meta.
        """
        # we have a lang attribute in html
        attr = self.parser.getAttribute(article.doc, attr='lang')
        if attr is None:
            # look up for a Content-Language in meta
            items = [
                {'tag': 'meta', 'attr': 'http-equiv', 'value': 'content-language'},
                {'tag': 'meta', 'attr': 'name', 'value': 'lang'}
            ]
            for item in items:
                meta = self.parser.getElementsByTag(article.doc, **item)
                if meta:
                    attr = self.parser.getAttribute(meta[0], attr='content')
                    break
        if attr:
            value = attr[:2]
            if re.search(RE_LANG, value):
                return value.lower()

        return None

    def get_meta_content(self, doc, metaName):
        """
        Extract a given meta content form document.
        """
        meta = self.parser.css_select(doc, metaName)
        content = None

        if meta is not None and len(meta) > 0:
            content = self.parser.getAttribute(meta[0], 'content')

        if content:
            return content.strip()

        return ''

    def get_meta_description(self, article):
        """
        If the article has meta description set in the source, use that.
        """
        return self.get_meta_content(article.doc, "meta[name=description]")

    def get_meta_keywords(self, article):
        """
        If the article has meta keywords set in the source, use that.
        """
        return self.get_meta_content(article.doc, "meta[name=keywords]")

    def get_canonical_link(self, article):
        """
        If the article has meta canonical link set in the url.
        """
        kwargs = {'tag': 'link', 'attr': 'rel', 'value': 'canonical'}
        meta = self.parser.getElementsByTag(article.doc, **kwargs)
        if meta is not None and len(meta) > 0:
            href = self.parser.getAttribute(meta[0], 'href')
            if href:
                href = href.strip()
                o = urlparse.urlparse(href)
                if not o.hostname:
                    z = urlparse.urlparse(article.url)
                    domain = '%s://%s' % (z.scheme, z.hostname)
                    href = urlparse.urljoin(domain, href)
                return href
        return u''

    def get_img_urls(self, article):
        """
        Return all of the images on an html page, lxml root.
        """
        doc = article.raw_doc
        urls = self.parser.get_img_urls(doc)
        img_links = [ urlparse.urljoin(article.url, url) for url in urls ]

        return img_links

    def get_top_img_url(self, article):
        """
        """
        # !important, we must use raw_doc because at this point doc has been cleaned
        doc = article.raw_doc
        return self.parser.get_top_img_url(doc)

    def get_category_urls(self, source, source_url=None, page_urls=None):
        """
        Requires: source lxml root and source url takes a domain and finds all of the
        top level urls, we are assuming that these are the category urls.

        cnn.com --> [cnn.com/latest, world.cnn.com, cnn.com/asia]
        """

        source_url = source.url if not source_url else source_url
        page_urls = self.parser.get_urls(source.doc) if not page_urls else page_urls
        valid_categories = []
        for p_url in page_urls:
            scheme = get_scheme(p_url, allow_fragments=False)
            domain = get_domain(p_url, allow_fragments=False)
            path = get_path(p_url, allow_fragments=False)

            if not domain and not path:
                if source.config.verbose:
                    print 'elim category url %s for no domain and path' % p_url
                continue
            if path and path.startswith('#'):
                if source.config.verbose:
                    print 'elim category url %s path starts with #' % p_url
                continue
            if scheme and (scheme!='http' and scheme!='https'):
                if source.config.verbose:
                    print 'elim category url %s for bad scheme, not http nor https' % p_url
                continue

            if domain:
                child_tld = tldextract.extract(p_url)
                domain_tld = tldextract.extract(source_url)

                child_subdomain_parts = child_tld.subdomain.split('.')
                subdomain_contains = False
                for part in child_subdomain_parts:
                    if part == domain_tld.domain:
                        if source.config.verbose:
                            print 'subdomain contains at %s and %s' % (str(part), str(domain_tld.domain))
                        subdomain_contains = True
                        break

                # microsoft.com is definitely not related to espn.com, but espn.go.com is probably
                # related to espn.com
                if not subdomain_contains and (child_tld.domain != domain_tld.domain):
                    if source.config.verbose:
                        print 'elim category url %s for domain mismatch' % p_url
                        continue
                elif child_tld.subdomain in ['m', 'i']:
                    if source.config.verbose:
                        print 'elim category url %s for mobile subdomain' % p_url
                    continue
                else:
                    valid_categories.append(scheme+'://'+domain)
                    # TODO account for case where category is in form http://subdomain.domain.tld/category/ <-- it's still legal!
            else:
                # we want a path with just one subdir
                # cnn.com/world and cnn.com/world/ are both valid_categories
                path_chunks = [ x for x in path.split('/') if len(x) > 0 ]

                if 'index.html' in path_chunks:
                    path_chunks.remove('index.html')

                if len(path_chunks) == 1 and len(path_chunks[0]) < 14:
                    valid_categories.append(domain+path)
                else:
                    if source.config.verbose:
                        print 'elim category url %s for >1 path chunks or size path chunks' % p_url


        stopwords = [
            'about', 'help', 'privacy', 'legal', 'feedback', 'sitemap',
            'profile', 'account', 'mobile', 'sitemap', 'facebook', 'myspace',
            'twitter', 'linkedin', 'bebo', 'friendster', 'stumbleupon', 'youtube',
            'vimeo', 'store', 'mail', 'preferences', 'maps', 'password', 'imgur',
            'flickr', 'search', 'subscription', 'itunes', 'siteindex', 'events',
            'stop', 'jobs', 'careers', 'newsletter', 'subscribe', 'academy',
            'shopping', 'purchase', 'site-map', 'shop', 'donate', 'newsletter',
            'product', 'advert', 'info', 'tickets', 'coupons', 'forum', 'board',
            'archive', 'browse', 'howto', 'how to', 'faq', 'terms', 'charts',
            'services', 'contact', 'plus', 'admin', 'login', 'signup', 'register',
            'developer', 'proxy']

        _valid_categories = []

        # TODO Stop spamming urlparse and tldextract calls...

        for p_url in valid_categories:
            path = get_path(p_url)
            subdomain = tldextract.extract(p_url).subdomain
            conjunction = path + ' ' + subdomain
            bad = False
            for badword in stopwords:
                if badword.lower() in conjunction.lower():
                    if source.config.verbose:
                        print 'elim category url %s for subdomain contain stopword!' % p_url
                    bad=True
                    break
            if not bad:
                _valid_categories.append(p_url)

        _valid_categories.append('/') # add the root!

        for i, p_url in enumerate(_valid_categories):
            if p_url.startswith('://') :
                p_url = 'http' + p_url
                _valid_categories[i] = p_url

            elif p_url.startswith('//'):
                p_url = 'http:' + p_url
                _valid_categories[i] = p_url

            if p_url.endswith('/'):
                p_url = p_url[:-1]
                _valid_categories[i] = p_url

        _valid_categories = list(set(_valid_categories))

        category_urls = [prepare_url(p_url, source_url) for p_url in _valid_categories]
        category_urls = [c for c in category_urls if c is not None]
        return category_urls

    def get_feed_urls(self, source):
        """
        Requires: List of category lxml roots, two types of anchors: categories
        and feeds (rss). we extract category urls first and then feeds.
        """
        feed_urls = []
        for category in source.categories:
            root = category.doc
            feed_urls.extend(self.parser.get_feed_urls(root))

        feed_urls = feed_urls[:50]
        feed_urls = [ prepare_url(f, source.url) for f in feed_urls ]

        feeds = list(set(feed_urls))
        return feeds

    def extract_tags(self, article):
        node = article.doc

        # node doesn't have chidren
        if len(list(node)) == 0:
            return NO_STRINGS

        elements = self.parser.css_select(node, A_REL_TAG_SELECTOR)
        if not elements:
            elements = self.parser.css_select(node, A_HREF_TAG_SELECTOR)
            if not elements:
                return NO_STRINGS

        tags = []
        for el in elements:
            tag = self.parser.getText(el)
            if tag:
                tags.append(tag)

        return set(tags)

    def calculate_best_node(self, article):
        doc = article.doc
        top_node = None
        nodes_to_check = self.nodes_to_check(doc)

        starting_boost = float(1.0)
        cnt = 0
        i = 0
        parent_nodes = []
        nodes_with_text = []

        for node in nodes_to_check:
            text_node = self.parser.getText(node)
            word_stats = self.stopwords_class(language=self.language).get_stopword_count(text_node)
            high_link_density = self.is_highlink_density(node)
            if word_stats.get_stopword_count() > 2 and not high_link_density:
                nodes_with_text.append(node)

        nodes_number = len(nodes_with_text)
        negative_scoring = 0
        bottom_negativescore_nodes = float(nodes_number) * 0.25

        for node in nodes_with_text:
            boost_score = float(0)
            # boost
            if(self.is_boostable(node)):
                if cnt >= 0:
                    boost_score = float((1.0 / starting_boost) * 50)
                    starting_boost += 1
            # nodes_number
            if nodes_number > 15:
                if (nodes_number - i) <= bottom_negativescore_nodes:
                    booster = float(bottom_negativescore_nodes - (nodes_number - i))
                    boost_score = float(-pow(booster, float(2)))
                    negscore = -abs(boost_score) + negative_scoring
                    if negscore > 40:
                        boost_score = float(5)

            text_node = self.parser.getText(node)
            word_stats = self.stopwords_class(language=self.language).get_stopword_count(text_node)
            upscore = int(word_stats.get_stopword_count() + boost_score)

            # parent node
            parent_node = self.parser.getParent(node)
            self.update_score(parent_node, upscore)
            self.update_node_count(parent_node, 1)

            if parent_node not in parent_nodes:
                parent_nodes.append(parent_node)

            # parent of parent node
            parent_parent_node = self.parser.getParent(parent_node)
            if parent_parent_node is not None:
                self.update_node_count(parent_parent_node, 1)
                self.update_score(parent_parent_node, upscore / 2)
                if parent_parent_node not in parent_nodes:
                    parent_nodes.append(parent_parent_node)
            cnt += 1
            i += 1

        top_node_score = 0
        for e in parent_nodes:
            score = self.get_score(e)

            if score > top_node_score:
                top_node = e
                top_node_score = score

            if top_node is None:
                top_node = e

        return top_node

    def is_boostable(self, node):
        """
        Alot of times the first paragraph might be the caption under an image
        so we'll want to make sure if we're going to boost a parent node that
        it should be connected to other paragraphs,
        at least for the first n paragraphs so we'll want to make sure that
        the next sibling is a paragraph and has at
        least some substantial weight to it.
        """
        para = "p"
        steps_away = 0
        minimum_stopword_count = 5
        max_stepsaway_from_node = 3

        nodes = self.walk_siblings(node)
        for current_node in nodes:
            # p
            current_node_tag = self.parser.getTag(current_node)
            if current_node_tag == para:
                if steps_away >= max_stepsaway_from_node:
                    return False
                paraText = self.parser.getText(current_node)
                word_stats = self.stopwords_class(language=self.language).get_stopword_count(paraText)
                if word_stats.get_stopword_count() > minimum_stopword_count:
                    return True
                steps_away += 1
        return False

    def walk_siblings(self, node):
        current_sibling = self.parser.previousSibling(node)
        b = []
        while current_sibling is not None:
            b.append(current_sibling)
            previousSibling = self.parser.previousSibling(current_sibling)
            current_sibling = None if previousSibling is None else previousSibling
        return b

    def add_siblings(self, top_node):
        baselinescore_siblings_para = self.get_siblings_score(top_node)
        results = self.walk_siblings(top_node)
        for current_node in results:
            ps = self.get_siblings_content(current_node, baselinescore_siblings_para)
            for p in ps:
                top_node.insert(0, p)
        return top_node

    def get_siblings_content(self, current_sibling, baselinescore_siblings_para):
        """
        Adds any siblings that may have a decent score to this node.
        """
        if current_sibling.tag == 'p' and len(self.parser.getText(current_sibling)) > 0:
            e0 = current_sibling
            if e0.tail:
                e0 = copy.deepcopy(e0)
                e0.tail = ''
            return [e0]
        else:
            potential_paragraphs = self.parser.getElementsByTag(current_sibling, tag='p')
            if potential_paragraphs is None:
                return None
            else:
                ps = []
                for first_paragraph in potential_paragraphs:
                    text = self.parser.getText(first_paragraph)
                    if len(text) > 0:
                        word_stats = self.stopwords_class(language=self.language).get_stopword_count(text)
                        paragraph_score = word_stats.get_stopword_count()
                        sibling_baseline_score = float(.30)
                        high_link_density = self.is_highlink_density(first_paragraph)
                        score = float(baselinescore_siblings_para * sibling_baseline_score)
                        if score < paragraph_score and not high_link_density:
                            p = self.parser.createElement(tag='p', text=text, tail=None)
                            ps.append(p)
                return ps

    def get_siblings_score(self, top_node):
        """
        We could have long articles that have tons of paragraphs
        so if we tried to calculate the base score against
        the total text score of those paragraphs it would be unfair.
        So we need to normalize the score based on the average scoring
        of the paragraphs within the top node.
        For example if our total score of 10 paragraphs was 1000
        but each had an average value of 100 then 100 should be our base.
        """
        base = 100000
        paragraphs_number = 0
        paragraphs_score = 0
        nodes_to_check = self.parser.getElementsByTag(top_node, tag='p')

        for node in nodes_to_check:
            text_node = self.parser.getText(node)
            word_stats = self.stopwords_class(language=self.language).get_stopword_count(text_node)
            high_link_density = self.is_highlink_density(node)
            if word_stats.get_stopword_count() > 2 and not high_link_density:
                paragraphs_number += 1
                paragraphs_score += word_stats.get_stopword_count()

        if paragraphs_number > 0:
            base = paragraphs_score / paragraphs_number

        return base

    def update_score(self, node, addToScore):
        """
        Adds a score to the gravityScore Attribute we put on divs
        we'll get the current score then add the score
        we're passing in to the current.
        """
        current_score = 0
        score_string = self.parser.getAttribute(node, 'gravityScore')
        if score_string:
            current_score = int(score_string)

        new_score = current_score + addToScore
        self.parser.setAttribute(node, "gravityScore", str(new_score))

    def update_node_count(self, node, add_to_count):
        """
        Stores how many decent nodes are under a parent node.
        """
        current_score = 0
        count_string = self.parser.getAttribute(node, 'gravityNodes')
        if count_string:
            current_score = int(count_string)

        new_score = current_score + add_to_count
        self.parser.setAttribute(node, "gravityNodes", str(new_score))

    def is_highlink_density(self, e):
        """
        Checks the density of links within a node,
        is there not much text and most of it contains linky shit?
        if so it's no good.
        """
        links = self.parser.getElementsByTag(e, tag='a')
        if links is None or len(links) == 0:
            return False

        text = self.parser.getText(e)
        words = text.split(' ')
        words_number = float(len(words))
        sb = []
        for link in links:
            sb.append(self.parser.getText(link))

        linkText = ''.join(sb)
        linkWords = linkText.split(' ')
        numberOfLinkWords = float(len(linkWords))
        numberOfLinks = float(len(links))
        linkDivisor = float(numberOfLinkWords / words_number)
        score = float(linkDivisor * numberOfLinks)
        if score >= 1.0:
            return True
        return False
        # return True if score > 1.0 else False

    def get_score(self, node):
        """
        Returns the gravityScore as an integer from this node.
        """
        return self.get_node_gravity_score(node) or 0

    def get_node_gravity_score(self, node):
        grvScoreString = self.parser.getAttribute(node, 'gravityScore')
        if not grvScoreString:
            return None
        return int(grvScoreString)

    def nodes_to_check(self, doc):
        """
        Returns a list of nodes we want to search
        on like paragraphs and tables.
        """
        nodes_to_check = []
        for tag in ['p', 'pre', 'td']:
            items = self.parser.getElementsByTag(doc, tag=tag)
            nodes_to_check += items
        return nodes_to_check

    def is_table_and_no_para_exist(self, e):
        subParagraphs = self.parser.getElementsByTag(e, tag='p')
        for p in subParagraphs:
            txt = self.parser.getText(p)
            if len(txt) < 25:
                self.parser.remove(p)

        subParagraphs2 = self.parser.getElementsByTag(e, tag='p')
        if len(subParagraphs2) == 0 and e.tag is not "td":
            return True
        return False

    def is_nodescore_threshold_met(self, node, e):
        top_node_score = self.get_score(node)
        current_nodeScore = self.get_score(e)
        thresholdScore = float(top_node_score * .08)

        if (current_nodeScore < thresholdScore) and e.tag != 'td':
            return False
        return True

    def post_cleanup(self, targetNode):
        """
        Remove any divs that looks like non-content,
        clusters of links, or paras with no gusto.
        """
        node = self.add_siblings(targetNode)
        for e in self.parser.getChildren(node):
            e_tag = self.parser.getTag(e)
            if e_tag != 'p':
                if self.is_highlink_density(e) \
                    or self.is_table_and_no_para_exist(e) \
                    or not self.is_nodescore_threshold_met(node, e):
                    self.parser.remove(e)
        return node


class StandardContentExtractor(ContentExtractor):
    pass
