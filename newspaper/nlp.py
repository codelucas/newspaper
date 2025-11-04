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
from os import path

from collections import Counter, OrderedDict
from operator import itemgetter

from . import settings

ideal = 20.0

stopwords = set()

def load_stopwords(language):
    """ 
    Loads language-specific stopwords for keyword selection
    """
    global stopwords
    
    # stopwords for nlp in English are not the regular stopwords
    # to pass the tests
    # can be changed with the tests
    if language == 'en':
        stopwordsFile = settings.NLP_STOPWORDS_EN
    else:
        stopwordsFile = path.join(settings.STOPWORDS_DIR,\
                                  'stopwords-{}.txt'.format(language))
    with open(stopwordsFile, 'r', encoding='utf-8') as f:
        stopwords.update(set([w.strip() for w in f.readlines()]))
        
        
def summarize(url='', title='', text='', max_sents=5):
    if not text or not title or max_sents <= 0:
        return []

    summaries = []
    sentences = split_sentences(text)
    keys = keywords(text)
    titleWords = split_words(title)

    # Score sentences, and use the top 5 or max_sents sentences
    ranks = score(sentences, titleWords, keys).most_common(max_sents)
    for rank in ranks:
        summaries.append(rank[0])
    summaries.sort(key=lambda summary: summary[0])
    return [summary[1] for summary in summaries]


def score(sentences, titleWords, keywords):
    """Score sentences based on different features
    """
    senSize = len(sentences)
    ranks = Counter()
    for i, s in enumerate(sentences):
        sentence = split_words(s)
        titleFeature = title_score(titleWords, sentence)
        sentenceLength = length_score(len(sentence))
        sentencePosition = sentence_position(i + 1, senSize)
        sbsFeature = sbs(sentence, keywords)
        dbsFeature = dbs(sentence, keywords)
        frequency = (sbsFeature + dbsFeature) / 2.0 * 10.0
        # Weighted average of scores from four categories
        totalScore = (titleFeature*1.5 + frequency*2.0 +
                      sentenceLength*1.0 + sentencePosition*1.0)/4.0
        ranks[(i, s)] = totalScore
    return ranks


def sbs(words, keywords):
    score = 0.0
    if (len(words) == 0):
        return 0
    for word in words:
        if word in keywords:
            score += keywords[word]
    return (1.0 / math.fabs(len(words)) * score) / 10.0


def dbs(words, keywords):
    if (len(words) == 0):
        return 0
    summ = 0
    first = []
    second = []

    for i, word in enumerate(words):
        if word in keywords:
            score = keywords[word]
            if first == []:
                first = [i, score]
            else:
                second = first
                first = [i, score]
                dif = first[0] - second[0]
                summ += (first[1] * second[1]) / (dif ** 2)
    # Number of intersections
    k = len(set(keywords.keys()).intersection(set(words))) + 1
    return (1 / (k * (k + 1.0)) * summ)


def split_words(text):
    """Split a string into array of words
    """
    try:
        text = re.sub(r'[^\w ]', '', text)  # strip special chars
        return [x.strip('.').lower() for x in text.split()]
    except TypeError:
        return None


def keywords(text):
    """Get the top 10 keywords and their frequency scores ignores blacklisted
    words in stopwords, counts the number of occurrences of each word, and
    sorts them in reverse natural order (so descending) by number of
    occurrences.
    """
    NUM_KEYWORDS = 10
    text = split_words(text)
    # of words before removing blacklist words
    if text:
        num_words = len(text)
        text = [x for x in text if x not in stopwords]
        freq = {}
        for word in text:
            if word in freq:
                freq[word] += 1
            else:
                freq[word] = 1

        min_size = min(NUM_KEYWORDS, len(freq))
        keywords = sorted(freq.items(),
                          key=lambda x: (x[1], x[0]),
                          reverse=True)
        keywords = keywords[:min_size]
        keywords = dict((x, y) for x, y in keywords)

        for k in keywords:
            articleScore = keywords[k] * 1.0 / max(num_words, 1)
            keywords[k] = articleScore * 1.5 + 1
        return dict(keywords)
    else:
        return dict()


def log_likelihood(length_target, length_reference, frequency_target, frequency_reference, significance_test=True):
    """Get the log-likelihood scores of all words in the target corpus. By default, only signficant (95th percentile) 
    results are returned. Based on Paul Raysons's log-likelihood and effect size calculator 
    (http://ucrel.lancs.ac.uk/llwizard.html)."""

    log_likelihood_scores = []

    for word, frequency in frequency_target.items():
        f_target = frequency_target[word]
        try:
            f_reference = frequency_reference[word]
        except KeyError:
            f_reference = 0

        expected_1 = length_target * (f_target + f_reference) / (length_target + length_reference)
        expected_2 = length_reference * (f_target + f_reference) / (length_target + length_reference)

        try:
            ll = 2 * (f_target * math.log((f_target / expected_1)) + (f_reference * math.log(f_reference / expected_2)))
        except ValueError:
            ll = 0

        if significance_test:
            # 95th percentile
            if ll > 3.84:
                log_likelihood_scores.append([word, ll])
        else:
            log_likelihood_scores.append([word, ll])

    return log_likelihood_scores


def keywords_reference_corpus(text, reference_corpus, use_stopwords=True):
    """Get the top 10 keywords based on a comparison with a reference corpus. 
    By default, stopwords are ignored."""

    NUM_KEYWORDS = 10
    with open(reference_corpus, 'r') as file:
        reference_corpus = file.read()

    text = split_words(text)

    if use_stopwords:
        text = [x for x in text if x not in stopwords]

    frequency_target = dict(Counter(text))
    length_target = len(text)
    frequency_reference = dict(Counter(split_words(reference_corpus)))
    length_reference = len(split_words(reference_corpus))

    log_likelihood_scores = log_likelihood(length_target, length_reference, frequency_target, frequency_reference)

    keywords = sorted(log_likelihood_scores, key=itemgetter(1), reverse=True)[:NUM_KEYWORDS]
    keywords = {word: ll for (word, ll) in keywords}

    return dict(keywords)


def split_sentences(text):
    """Split a large string into sentences
    """
    import nltk.data
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

    sentences = tokenizer.tokenize(text)
    sentences = [x.replace('\n', '') for x in sentences if len(x) > 10]
    return sentences


def length_score(sentence_len):
    return 1 - math.fabs(ideal - sentence_len) / ideal


def title_score(title, sentence):
    if title:
        title = [x for x in title if x not in stopwords]
        count = 0.0
        for word in sentence:
            if (word not in stopwords and word in title):
                count += 1.0
        return count / max(len(title), 1)
    else:
        return 0


def sentence_position(i, size):
    """Different sentence positions indicate different
    probability of being an important sentence.
    """
    normalized = i * 1.0 / size
    if (normalized > 1.0):
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
