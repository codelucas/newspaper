# -*- coding: utf-8 -*-
"""
Stopword extraction and stopword classes.
"""
__title__ = 'newspaper'
__author__ = 'Lucas Ou-Yang'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014, Lucas Ou-Yang'

import os
import re
import string

from .utils import FileHelper

TABSSPACE = re.compile(r'[\s\t]+')


def innerTrim(value):
    if isinstance(value, str):
        # remove tab and white space
        value = re.sub(TABSSPACE, ' ', value)
        value = ''.join(value.splitlines())
        return value.strip()
    return ''


class WordStats(object):

    def __init__(self):
        # total number of stopwords or good words we calc
        self.stop_word_count = 0

        # total number of words on a node
        self.word_count = 0

        # holds an actual list of stop words we have
        self.stop_words = []

    def get_stop_words(self):
        return self.stop_words

    def set_stop_words(self, words):
        self.stop_words = words

    def get_stopword_count(self):
        return self.stop_word_count

    def set_stopword_count(self, wordcount):
        self.stop_word_count = wordcount

    def get_word_count(self):
        return self.word_count

    def set_word_count(self, cnt):
        self.word_count = cnt


class StopWords(object):

    TRANS_TABLE = str.maketrans('', '')
    _cached_stop_words = {}

    def __init__(self, language='en'):
        if language not in self._cached_stop_words:
            path = os.path.join('text', 'stopwords-%s.txt' % language)
            self._cached_stop_words[language] = \
                set(FileHelper.loadResourceFile(path).splitlines())
        self.STOP_WORDS = self._cached_stop_words[language]

    def remove_punctuation(self, content):
        # code taken form
        # http://stackoverflow.com/questions/265960/best-way-to-strip-punctuation-from-a-string-in-python
        content_is_unicode = isinstance(content, str)
        if content_is_unicode:
            content = content.encode('utf-8')
        trans_table = {ord(c): None for c in string.punctuation}
        stripped_input = content.decode('utf-8').translate(trans_table)

        return stripped_input

    def candidate_words(self, stripped_input):
        return stripped_input.split(' ')

    def get_stopword_count(self, content):
        if not content:
            return WordStats()
        ws = WordStats()
        stripped_input = self.remove_punctuation(content)
        candidate_words = self.candidate_words(stripped_input.lower())
        overlapping_stopwords = []
        c = 0
        for w in candidate_words:
            c += 1
            if w in self.STOP_WORDS:
                overlapping_stopwords.append(w)

        ws.set_word_count(c)
        ws.set_stopword_count(len(overlapping_stopwords))
        ws.set_stop_words(overlapping_stopwords)
        return ws


class StopWordsChinese(StopWords):
    """Chinese segmentation
    """
    def __init__(self, language='zh'):
        super(StopWordsChinese, self).__init__(language='zh')

    def candidate_words(self, stripped_input):
        # jieba builds a tree that takes a while. avoid building
        # this tree if we don't use the chinese language
        import jieba
        return jieba.cut(stripped_input, cut_all=True)


class StopWordsArabic(StopWords):
    """Arabic segmentation
    """
    def __init__(self, language='ar'):
        # force ar languahe code
        super(StopWordsArabic, self).__init__(language='ar')

    def remove_punctuation(self, content):
        return content

    def candidate_words(self, stripped_input):
        import nltk
        s = nltk.stem.isri.ISRIStemmer()
        words = []
        for word in nltk.tokenize.wordpunct_tokenize(stripped_input):
            words.append(s.stem(word))
        return words


class StopWordsKorean(StopWords):
    """Korean segmentation
    """
    def __init__(self, language='ko'):
        super(StopWordsKorean, self).__init__(language='ko')

    def get_stopword_count(self, content):
        if not content:
            return WordStats()
        ws = WordStats()
        stripped_input = self.remove_punctuation(content)
        candidate_words = self.candidate_words(stripped_input)
        overlapping_stopwords = []
        c = 0
        for w in candidate_words:
            c += 1
            for stop_word in self.STOP_WORDS:
                overlapping_stopwords.append(stop_word)

        ws.set_word_count(c)
        ws.set_stopword_count(len(overlapping_stopwords))
        ws.set_stop_words(overlapping_stopwords)
        return ws


class StopWordsHindi(StopWords):
    """Hindi segmentation
    """
    def __init__(self, language='hi'):
        super(StopWordsHindi, self).__init__(language='hi')

    def get_stopword_count(self, content):
        if not content:
            return WordStats()
        ws = WordStats()
        stripped_input = self.remove_punctuation(content)
        candidate_words = self.candidate_words(stripped_input)
        overlapping_stopwords = []
        c = 0
        for w in candidate_words:
            c += 1
            for stop_word in self.STOP_WORDS:
                overlapping_stopwords.append(stop_word)

        ws.set_word_count(c)
        ws.set_stopword_count(len(overlapping_stopwords))
        ws.set_stop_words(overlapping_stopwords)
        return ws
