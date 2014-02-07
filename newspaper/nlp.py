# -*- coding: utf-8 -*-
"""
Anything natural language related should be abstracted into this file.
"""
__title__ = 'newspaper'
__author__ = 'Lucas Ou-Yang'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014, Lucas Ou-Yang'

import re
import math

from collections import Counter, OrderedDict
from . import settings

with open(settings.NLP_STOPWORDS_EN, 'r') as f:
    stopwords = [ w.strip() for w in f.readlines()]

ideal = 20.0

def summarize(url='', title='', text=''):
    """
    """
    if (text == '' or title == ''):
        return []

    #if isinstance(title, str):
    #    title = title.encode('utf-8', 'ignore')

    #if isinstance(text, str):
    #    text = text.encode('utf-8', 'ignore')

    summaries = []
    sentences = split_sentences(text)
    keys = keywords(text)
    titleWords = split_words(title)

    # score setences, and use the top 5 sentences
    ranks = score(sentences, titleWords, keys).most_common(5)
    for rank in ranks:
        summaries.append(rank[0])

    return summaries

def score(sentences, titleWords, keywords):
    """
    Score sentences based on different features.
    """
    senSize = len(sentences)
    ranks = Counter()
    for i, s in enumerate(sentences):
        sentence = split_words(s)
        titleFeature = title_score(titleWords, sentence)
        sentenceLength = length_score(len(sentence))
        sentencePosition = sentence_position(i+1, senSize)
        sbsFeature = sbs(sentence, keywords)
        dbsFeature = dbs(sentence, keywords)
        frequency = (sbsFeature + dbsFeature) / 2.0 * 10.0

        # weighted average of scores from four categories
        totalScore = (titleFeature*1.5 + frequency*2.0 +
                      sentenceLength*1.0 + sentencePosition*1.0)/4.0
        ranks[s] = totalScore
    return ranks

def sbs(words, keywords):
    """
    """
    score = 0.0
    if (len(words) == 0):
        return 0
    for word in words:
        if word in keywords:
            score += keywords[word]
    return (1.0 / math.fabs(len(words)) * score)/10.0

def dbs(words, keywords):
    """
    """
    if (len(words)==0):
        return 0
    summ = 0
    first = []
    second = []

    for i, word in enumerate(words):
        if word in keywords:
            score = keywords[word]
            if first==[]:
                first = [i, score]
            else:
                second = first
                first = [i, score]
                dif = first[0] - second[0]
                summ+=(first[1]*second[1]) / (dif ** 2)

    # number of intersections
    k = len(set(keywords.keys()).intersection(set(words)))+1
    return (1/(k*(k+1.0))*summ)

def split_words(text):
    """
    Split a string into array of words.
    """
    try:
        text = re.sub(r'[^\w ]', '', text) #strip special chars
        return [x.strip('.').lower() for x in text.split()]
    except TypeError:
        return None

def keywords(text):
    """
    Get the top 10 keywords and their frequency scores ignores blacklisted
    words in stopwords, counts the number of occurrences of each word, and
    sorts them in reverse natural order (so descending) by number of occurrences.
    """
    import operator # sorting
    text = split_words(text)
    # of words before removing blacklist words
    num_words = len(text)
    text = [x for x in text if x not in stopwords]
    freq = Counter()
    for word in text:
        freq[word]+=1

    minSize = min(10, len(freq))
    keywords = tuple(freq.most_common(minSize)) # get first 10
    keywords = dict((x,y) for x, y in keywords) # recreate a dict

    for k in keywords:
        articleScore = keywords[k]*1.0 / max(num_words, 1)
        keywords[k] = articleScore * 1.5 + 1

    keywords = sorted(iter(keywords.items()), key=operator.itemgetter(1))
    keywords.reverse()
    return dict(keywords)

def split_sentences(text):
    """
    Split a large string into sentences.
    """
    import nltk.data
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

    # text = re.sub(r'[^\w .]', '', text)
    sentences = tokenizer.tokenize(text)
    sentences = [x.replace('\n','') for x in sentences if len(x)>10]
    return sentences

def length_score(sentence_len):
    """
    """
    return 1- math.fabs(ideal - sentence_len) / ideal

def title_score(title, sentence):
    """
    """
    title = [x for x in title if x not in stopwords]
    count = 0.0
    for word in sentence:
        if (word not in stopwords and word in title):
            count+=1.0
    return count / max(len(title), 1)

def sentence_position(i, size):
    """
    Different sentence positions indicate different
    probability of being an important sentence.
    """
    normalized =  i*1.0 / size
    if (normalized > 1.0): #just in case
        return 0
    elif (normalized > 0.9):
        return 0.15
    elif (normalized > 0.8):
        return 0.04
    elif (normalized > 0.7):
        return 0.04
    elif (normalized > 0.6):
        return 0.06
    elif (normalized > 0.5):
        return 0.04
    elif (normalized > 0.4):
        return 0.05
    elif (normalized > 0.3):
        return 0.08
    elif (normalized > 0.2):
        return 0.14
    elif (normalized > 0.1):
        return 0.23
    elif (normalized > 0):
        return 0.17
    else:
        return 0

