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
import os
import json
import hashlib
import unittest

from base import MockResponse
from extractors import TestExtractionBase

from goose.configuration import Configuration
from goose.images.image import Image
from goose.images.image import ImageDetails
from goose.images.utils import ImageUtils
from goose.utils import FileHelper

CURRENT_PATH = os.path.dirname(os.path.abspath(__file__))


class MockResponseImage(MockResponse):

    def image_content(self, req):
        md5_hash = hashlib.md5(req.get_full_url()).hexdigest()
        current_test = self.cls._get_current_testname()
        path = os.path.join(CURRENT_PATH, "data", "images", current_test, md5_hash)
        path = os.path.abspath(path)
        f = open(path, 'rb')
        content = f.read()
        f.close()
        return content

    def html_content(self, req):
        current_test = self.cls._get_current_testname()
        path = os.path.join(CURRENT_PATH, "data", "images", current_test, "%s.html" % current_test)
        path = os.path.abspath(path)
        return FileHelper.loadResourceFile(path)

    def content(self, req):
        if self.cls.data['url'] == req.get_full_url():
            return self.html_content(req)
        return self.image_content(req)


class ImageExtractionTests(TestExtractionBase):
    """\
    Base Mock test case
    """
    callback = MockResponseImage

    def loadData(self):
        """\

        """
        suite, module, cls, func = self.id().split('.')
        path = os.path.join(CURRENT_PATH, "data", module, func, "%s.json" % func)
        path = os.path.abspath(path)
        content = FileHelper.loadResourceFile(path)
        self.data = json.loads(content)

    def getConfig(self):
        config = Configuration()
        config.enable_image_fetching = True
        return config

    def getExpectedImage(self, expected_value):
        image = Image()
        for k, v in expected_value.items():
            setattr(image, k, v)
        return image

    def assert_top_image(self, fields, expected_value, result_image):
        # test if the result value
        # is an Goose Image instance
        msg = u"Result value is not a Goose Image instance"
        self.assertTrue(isinstance(result_image, Image), msg=msg)

        # expected image
        expected_image = self.getExpectedImage(expected_value)
        msg = u"Expected value is not a Goose Image instance"
        self.assertTrue(isinstance(expected_image, Image), msg=msg)

        # check
        msg = u"Returned Image is not the one expected"
        self.assertEqual(expected_image.src, result_image.src, msg=msg)

        fields = vars(expected_image)
        for k, v in fields.items():
            msg = u"Returned Image attribute %s is not the one expected" % k
            self.assertEqual(getattr(expected_image, k), getattr(result_image, k), msg=msg)

    def test_basic_image(self):
        article = self.getArticle()
        fields = ['top_image']
        self.runArticleAssertions(article=article, fields=fields)

    def _test_known_image_css(self, article):
        # check if we have an image in article.top_node
        images = self.parser.getElementsByTag(article.top_node,  tag='img')
        self.assertEqual(len(images), 0)

        # we dont' have an image in article.top_node
        # check if the correct image was retrieved
        # using the known-image-css.txt
        fields = ['cleaned_text', 'top_image']
        self.runArticleAssertions(article=article, fields=fields)

    def test_known_image_name_parent(self):
        article = self.getArticle()
        self._test_known_image_css(article)

    def test_known_image_css_parent_class(self):
        article = self.getArticle()
        self._test_known_image_css(article)

    def test_known_image_css_parent_id(self):
        article = self.getArticle()
        self._test_known_image_css(article)

    def test_known_image_css_class(self):
        article = self.getArticle()
        self._test_known_image_css(article)

    def test_known_image_css_id(self):
        article = self.getArticle()
        self._test_known_image_css(article)

    def test_known_image_empty_src(self):
        'Tests that img tags for known image sources with empty src attributes are skipped.'
        article = self.getArticle()
        self._test_known_image_css(article)

    def test_opengraph_tag(self):
        article = self.getArticle()
        self._test_known_image_css(article)


class ImageUtilsTests(unittest.TestCase):

    def setUp(self):
        self.path = 'tests/data/images/test_basic_image/50850547cc7310bc53e30e802c6318f1'
        self.expected_results = {
            'width': 476,
            'height': 317,
            'mime_type': 'JPEG'
        }

    def test_utils_get_image_dimensions(self):
        image_detail = ImageUtils.get_image_dimensions(None, self.path)

        # test if we have an ImageDetails instance
        self.assertTrue(isinstance(image_detail, ImageDetails))

        # test image_detail attribute
        for k, v in self.expected_results.items():
            self.assertEqual(getattr(image_detail, k), v)

    def test_detail(self):
        image_detail = ImageUtils.get_image_dimensions(None, self.path)

        # test if we have an ImageDetails instance
        self.assertTrue(isinstance(image_detail, ImageDetails))

        # test image_detail attribute
        for k, v in self.expected_results.items():
            self.assertEqual(getattr(image_detail, k), v)

        # test image_detail get_ methode
        for k, v in self.expected_results.items():
            attr = 'get_%s' % k
            self.assertEqual(getattr(image_detail, attr)(), v)

        # test image_detail set_ methode
        expected_results = {
            'width': 10,
            'height': 10,
            'mime_type': 'PNG'
        }

        for k, v in expected_results.items():
            attr = 'set_%s' % k
            getattr(image_detail, attr)(v)

        for k, v in expected_results.items():
            attr = 'get_%s' % k
            self.assertEqual(getattr(image_detail, attr)(), v)
