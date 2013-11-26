# -*- coding: utf-8 -*-


import re
import math
from collections import Counter
from collections import OrderedDict

stopWords = ["-", " ", ",", ".", "a", "e", "i", "o", "u", "t", "about", "above", "above", "across", "after", "afterwards", "again", "against", "all", "almost", "alone", "along", "already", "also", "although", "always", "am", "among", "amongst", "amoungst", "amount", "an", "and", "another", "any", "anyhow", "anyone", "anything", "anyway", "anywhere", "are", "around", "as", "at", "back", "be", "became", "because", "become", "becomes", "becoming", "been", "before", "beforehand", "behind", "being", "below", "beside", "besides", "between", "beyond", "both", "bottom", "but", "by", "call", "can", "cannot", "can't", "co", "con", "could", "couldn't", "de", "describe", "detail", "did", "do", "done", "down", "due", "during", "each", "eg", "eight", "either", "eleven", "else", "elsewhere", "empty", "enough", "etc", "even", "ever", "every", "everyone", "everything", "everywhere", "except", "few", "fifteen", "fifty", "fill", "find", "fire", "first", "five", "for", "former", "formerly", "forty", "found", "four", "from", "front", "full", "further", "get", "give", "go", "got", "had", "has", "hasnt", "have", "he", "hence", "her", "here", "hereafter", "hereby", "herein", "hereupon", "hers", "herself", "him", "himself", "his", "how", "however", "hundred", "i", "ie", "if", "in", "inc", "indeed", "into", "is", "it", "its", "it's", "itself", "just", "keep", "last", "latter", "latterly", "least", "less", "like", "ltd", "made", "make", "many", "may", "me", "meanwhile", "might", "mill", "mine", "more", "moreover", "most", "mostly", "move", "much", "must", "my", "myself", "name", "namely", "neither", "never", "nevertheless", "new", "next", "nine", "no", "nobody", "none", "noone", "nor", "not", "nothing", "now", "nowhere", "of", "off", "often", "on", "once", "one", "only", "onto", "or", "other", "others", "otherwise", "our", "ours", "ourselves", "out", "over", "own", "part", "people", "per", "perhaps", "please", "put", "rather", "re", "said", "same", "see", "seem", "seemed", "seeming", "seems", "several", "she", "should", "show", "side", "since", "sincere", "six", "sixty", "so", "some", "somehow", "someone", "something", "sometime", "sometimes", "somewhere", "still", "such", "take", "ten", "than", "that", "the", "their", "them", "themselves", "then", "thence", "there", "thereafter", "thereby", "therefore", "therein", "thereupon", "these", "they", "thickv", "thin", "third", "this", "those", "though", "three", "through", "throughout", "thru", "thus", "to", "together", "too", "top", "toward", "towards", "twelve", "twenty", "two", "un", "under", "until", "up", "upon", "us", "use", "very", "via", "want", "was", "we", "well", "were", "what", "whatever", "when", "whence", "whenever", "where", "whereafter", "whereas", "whereby", "wherein", "whereupon", "wherever", "whether", "which", "while", "whither", "who", "whoever", "whole", "whom", "whose", "why", "will", "with", "within", "without", "would", "yet", "you", "your", "yours", "yourself", "yourselves", "the", "reuters", "news", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "mon", "tue", "wed", "thu", "fri", "sat", "sun", "rappler", "rapplercom", "inquirer", "yahoo", "home", "sports", "1", "10", "2012", "sa", "says", "tweet", "pm", "home", "homepage", "sports", "section", "newsinfo", "stories", "story", "photo", "2013", "na", "ng", "ang", "year", "years", "percent", "ko", "ako", "yung", "yun", "2", "3", "4", "5", "6", "7", "8", "9", "0", "time", "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december", "philippine", "government", "police", "manila"];

ideal = 20.0

def summarize(url='', title='', text=''):
    """"""

    article = None

    if title == '' or text == '':
        return None

    a_title, a_text = '', ''
    if article is not None:
        a_title = article.title
        a_text = article.cleaned_text

    text = a_text or text
    title = a_title or title

    if (text == '' or title == ''):
        return None

    if isinstance(title, unicode):
        title = title.encode('utf-8', 'ignore')

    if isinstance(text, unicode):
        text = text.encode('utf-8', 'ignore')

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
    """score sentences based on different features"""

    senSize = len(sentences)
    ranks = Counter()
    for i, s in enumerate(sentences):
        sentence = split_words(s)
        titleFeature = title_score(titleWords, sentence)
        sentenceLength = length_score(sentence)
        sentencePosition = sentence_position(i+1, senSize)
        sbsFeature = sbs(sentence, keywords)
        dbsFeature = dbs(sentence, keywords)
        frequency = (sbsFeature + dbsFeature) / 2.0 * 10.0

        # weighted average of scores from four categories
        totalScore = (titleFeature*1.5 + frequency*2.0 + sentenceLength*1.0 + sentencePosition*1.0)/4.0
        ranks[s] = totalScore
    return ranks


def sbs(words, keywords):
    """"""

    score = 0.0
    if (len(words) == 0):
        return 0
    for word in words:
        if word in keywords:
            score += keywords[word]
    return (1.0 / math.fabs(len(words)) * score)/10.0


def dbs(words, keywords):
    """"""

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
    """split a string into array of words"""
    try:
        text = re.sub(r'[^\w ]', '', text) #strip special chars
        return [x.strip('.').lower() for x in text.split()]
    except TypeError:
        return None


def keywords(text):
    #get the top 10 keywords and their frequency scores
    #ignores blacklisted words in stopWords,
    #counts the number of occurrences of each word,
    #and sorts them in reverse natural order (so descending) by number of occurrences

    import operator # sorting
    text = split_words(text)
    numWords = len(text) # of words before removing blacklist words
    text = [x for x in text if x not in stopWords]
    freq = Counter()
    for word in text:
        freq[word]+=1

    minSize = min(10, len(freq))
    keywords = tuple(freq.most_common(minSize)) # get first 10
    keywords = dict((x,y) for x, y in keywords) # recreate a dict

    for k in keywords:
        articleScore = keywords[k]*1.0 / numWords
        keywords[k] = articleScore * 1.5 + 1

    keywords = sorted(keywords.iteritems(), key=operator.itemgetter(1))
    keywords.reverse()
    return dict(keywords)


def split_sentences(text):
    """split a large string into sentences"""
    import nltk.data
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

    #text = re.sub(r'[^\w .]', '', text)
    sentences = tokenizer.tokenize(text)
    sentences = [x.replace('\n','') for x in sentences if len(x)>10]
    return sentences


def length_score(sentence):
    return 1- math.fabs(ideal - len(sentence)) / ideal


def title_score(title, sentence):
    title = [x for x in title if x not in stopWords]
    count = 0.0
    for word in sentence:
        if (word not in stopWords and word in title):
            count+=1.0
    return count/len(title)


def sentence_position(i, size):
    """different sentence positions indicate different probability of being an important sentence"""

    normalized =  i*1.0 / size
    if (normalized > 0 and normalized <= 0.1):
        return 0.17
    elif normalized > 0.1 and normalized <= 0.2:
        return 0.23
    elif (normalized > 0.2 and normalized <= 0.3):
        return 0.14
    elif (normalized > 0.3 and normalized <= 0.4):
        return 0.08
    elif (normalized > 0.4 and normalized <= 0.5):
        return 0.05
    elif (normalized > 0.5 and normalized <= 0.6):
        return 0.04
    elif (normalized > 0.6 and normalized <= 0.7):
        return 0.06
    elif (normalized > 0.7 and normalized <= 0.8):
        return 0.04
    elif (normalized > 0.8 and normalized <= 0.9):
        return 0.04
    elif (normalized > 0.9 and normalized <= 1.0):
        return 0.15
    else:
        return 0

