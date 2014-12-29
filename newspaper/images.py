# -*- coding: utf-8 -*-
"""
The following image extraction implementation was taken from an old
copy of Reddit's source code.
"""
__title__ = 'newspaper'
__author__ = 'Lucas Ou-Yang'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014, Lucas Ou-Yang'

import logging
import math
import StringIO
import traceback
import urllib
import urllib2

from httplib import InvalidURL
from PIL import Image, ImageFile

from . import urls

log = logging.getLogger(__name__)

chunk_size = 1024
thumbnail_size = 90, 90
minimal_area = 5000


def image_to_str(image):
    s = StringIO.StringIO()
    image.save(s, image.format)
    s.seek(0)
    return s.read()


def str_to_image(s):
    s = StringIO.StringIO(s)
    s.seek(0)
    image = Image.open(s)
    return image


def prepare_image(image):
    image = square_image(image)
    image.thumbnail(thumbnail_size, Image.ANTIALIAS)
    return image


def image_entropy(img):
    """ Calculate the entropy of an image
    """
    hist = img.histogram()
    hist_size = sum(hist)
    hist = [float(h) / hist_size for h in hist]
    return -sum([p * math.log(p, 2) for p in hist if p != 0])


def square_image(img):
    """If the image is taller than it is wide, square it off. determine
    which pieces to cut off based on the entropy pieces
    """
    x, y = img.size
    while y > x:
        # Slice 10px at a time until square
        slice_height = min(y - x, 10)
        bottom = img.crop((0, y - slice_height, x, y))
        top = img.crop((0, 0, x, slice_height))
        # remove the slice with the least entropy
        if image_entropy(bottom) < image_entropy(top):
            img = img.crop((0, 0, x, y - slice_height))
        else:
            img = img.crop((0, slice_height, x, y))
        x, y = img.size
    return img


def clean_url(url):
    """Url quotes unicode data out of urls
    """
    url = url.encode('utf8')
    url = ''.join([urllib.quote(c) if ord(c) >= 127 else c for c in url])
    return url


def fetch_url(url, useragent, referer=None, retries=1, dimension=False):
    cur_try = 0
    nothing = None if dimension else (None, None)
    url = clean_url(url)
    if not url.startswith(('http://', 'https://')):
        return nothing
    while True:
        try:
            req = urllib2.Request(url)
            req.add_header('User-Agent', useragent)
            if referer:
                req.add_header('Referer', referer)

            opener = urllib2.build_opener()
            open_req = opener.open(req, timeout=5)

            # if we only need the dimension of the image, we may not
            # need to download the entire thing
            if dimension:
                content = open_req.read(chunk_size)
            else:
                content = open_req.read()

            content_type = open_req.headers.get('content-type')

            if not content_type:
                return nothing

            if 'image' in content_type:
                p = ImageFile.Parser()
                new_data = content
                while not p.image and new_data:
                    try:
                        p.feed(new_data)
                    except IOError:
                        traceback.print_exc()
                        p = None
                        break
                    except ValueError:
                        traceback.print_exc()
                        p = None
                        break
                    except Exception as e:
                        # For some favicon.ico images, the image is so small
                        # that our PIL feed() method fails a length test.
                        is_favicon = (urls.url_to_filetype(url) == 'ico')
                        if is_favicon:
                            pass
                        else:
                            raise e
                        p = None
                        break
                    new_data = open_req.read(chunk_size)
                    content += new_data

                if p is None:
                    return nothing
                # return the size, or return the data
                if dimension and p.image:
                    return p.image.size
                elif dimension:
                    return nothing
            elif dimension:
                # expected an image, but didn't get one
                return nothing

            return content_type, content

        except (urllib2.URLError, urllib2.HTTPError, InvalidURL), e:
            cur_try += 1
            if cur_try >= retries:
                log.debug('error while fetching: %s refer: %s' %
                          (url, referer))
                return nothing
        finally:
            if 'open_req' in locals():
                open_req.close()


def fetch_image_dimension(url, useragent, referer=None, retries=1):
    return fetch_url(url, useragent, referer, retries, dimension=True)


class Scraper:

    def __init__(self, article):
        self.url = article.url
        self.imgs = article.imgs
        self.top_img = article.top_img
        self.config = article.config
        self.useragent = self.config.browser_user_agent

    def largest_image_url(self):
        # TODO: remove. it is not responsibility of Scrapper
        if not self.imgs and not self.top_img:
            return None
        if self.top_img:
            return self.top_img

        max_area = 0
        max_url = None
        for img_url in self.imgs:
            dimension = fetch_image_dimension(
                img_url, self.useragent, referer=self.url)
            area = self.calculate_area(img_url, dimension)
            if area > max_area:
                max_area = area
                max_url = img_url
        log.debug('using max img ' + max_url)
        return max_url

    def calculate_area(self, img_url, dimension):
        if not dimension:
            return 0
        area = dimension[0] * dimension[1]
        # Ignore tiny images
        if area < minimal_area:
            log.debug('ignore little %s' % img_url)
            return 0
        # PIL won't scale up, so set a min width and
        # maintain the aspect ratio
        if dimension[0] < thumbnail_size[0]:
            return 0
        # Ignore excessively long/wide images
        current_ratio = max(dimension) / min(dimension)
        if current_ratio > self.config.image_dimension_ration:
            log.debug('ignore dims %s' % img_url)
            return 0
        # Penalize images with "sprite" in their name
        lower_case_url = img_url.lower()
        if 'sprite' in lower_case_url or 'logo' in lower_case_url:
            log.debug('penalizing sprite %s' % img_url)
            area /= 10
        return area

    def satisfies_requirements(self, img_url):
        dimension = fetch_image_dimension(
            img_url, self.useragent, referer=self.url)
        area = self.calculate_area(img_url, dimension)
        return area > minimal_area

    def thumbnail(self):
        """Identifies top image, trims out a thumbnail and also has a url
        """
        image_url = self.largest_image_url()
        if image_url:
            content_type, image_str = fetch_url(image_url, referer=self.url)
            if image_str:
                image = str_to_image(image_str)
                try:
                    image = prepare_image(image)
                except IOError, e:
                    if 'interlaced' in e.message:
                        return None
                return image, image_url
        return None, None
