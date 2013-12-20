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
import hashlib
import os
import urllib2
from PIL import Image
from goose.utils.encoding import smart_str
from goose.images.image import ImageDetails
from goose.images.image import LocallyStoredImage


class ImageUtils(object):

    @classmethod
    def get_image_dimensions(self, identify_program, path):
        image = Image.open(path)
        image_details = ImageDetails()
        image_details.set_mime_type(image.format)
        width, height = image.size
        image_details.set_width(width)
        image_details.set_height(height)
        return image_details

    @classmethod
    def store_image(self, http_client, link_hash, src, config):
        """\
        Writes an image src http string to disk as a temporary file
        and returns the LocallyStoredImage object
        that has the info you should need on the image
        """
        # check for a cache hit already on disk
        image = self.read_localfile(link_hash, src, config)
        if image:
            return image

        # no cache found download the image
        data = self.fetch(http_client, src)
        if data:
            image = self.write_localfile(data, link_hash, src, config)
            if image:
                return image

        return None

    @classmethod
    def get_mime_type(self, image_details):
        mime_type = image_details.get_mime_type().lower()
        mimes = {
            'png': '.png',
            'jpg': '.jpg',
            'jpeg': '.jpg',
            'gif': '.gif',
        }
        return mimes.get(mime_type, 'NA')

    @classmethod
    def read_localfile(self, link_hash, src, config):
        local_image_name = self.get_localfile_name(link_hash, src, config)
        if os.path.isfile(local_image_name):
            identify = config.imagemagick_identify_path
            image_details = self.get_image_dimensions(identify, local_image_name)
            file_extension = self.get_mime_type(image_details)
            bytes = os.path.getsize(local_image_name)
            return LocallyStoredImage(
                src=src,
                local_filename=local_image_name,
                link_hash=link_hash,
                bytes=bytes,
                file_extension=file_extension,
                height=image_details.get_height(),
                width=image_details.get_width()
            )
        return None

    @classmethod
    def write_localfile(self, entity, link_hash, src, config):
        local_path = self.get_localfile_name(link_hash, src, config)
        f = open(local_path, 'wb')
        f.write(entity)
        f.close()
        return self.read_localfile(link_hash, src, config)

    @classmethod
    def get_localfile_name(self, link_hash, src, config):
        image_hash = hashlib.md5(smart_str(src)).hexdigest()
        return os.path.join(config.local_storage_path, '%s_%s' % (link_hash, image_hash))

    @classmethod
    def clean_src_string(self, src):
        return src.replace(" ", "%20")

    @classmethod
    def fetch(self, http_client, src):
        try:
            req = urllib2.Request(src)
            f = urllib2.urlopen(req)
            data = f.read()
            return data
        except:
            return None
