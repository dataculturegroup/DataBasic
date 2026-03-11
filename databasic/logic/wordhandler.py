"""
Word count utilities for DataBasic.

This module provides helpers for:
- tokenizing text into words
- counting words, bigrams, and trigrams
- optionally removing stop words
- sorting frequency distributions
"""

# Standard library imports
import logging
import re
import string
from operator import itemgetter

# Third-party imports
import nltk
from nltk import FreqDist

# Local imports
import databasic.logic.stopwords as stopwords

# Module-level logger
logger = logging.getLogger(__name__)

# Constants
DEFAULT_TEXT = (
    "I am Sam\n"
    "Sam I am\n"
    "That Sam-I-am!\n"
    "That Sam-I-am!\n"
    "I do not like that Sam-I-am!\n"
    "Do you like \n"
    "green eggs and ham?\n"
    "I do not like them, Sam-I-am.\n"
    "I do not like\n"
    "green eggs and ham.\n"
    "Would you like them \n"
    "here or there?\n"
    "I would not like them\n"
    "here or there.\n"
    "I would not like them anywhere."
)

MAX_ITEMS = 10000


def get_word_counts(
    text=None,
    ignore_case=True,
    ignore_stop_words=True,
    stopwords_language="english",
    get_bigrams=True,
    get_trigrams=True,
):
    """
    Return word, bigram, and trigram counts for the given text.

    Returns
    -------
    dict
        {
            "unique_words": list[(word, count)],
            "bigrams": list[((word1, word2), count)],
            "trigrams": list[((word1, word2, word3), count)],
            "total_word_count": int
        }
    """
    text = DEFAULT_TEXT if text is None else text
    words = _create_words(text, ignore_case)

    total_word_count = len(words)
    unique_words = _sort_count_list(
        _count_words(words, ignore_stop_words, stopwords_language)
    )[:MAX_ITEMS]

    if get_bigrams:
        bigrams = _sort_count_list(_count_bigrams(words))[:MAX_ITEMS]
    else:
        bigrams = []

    if get_trigrams:
        trigrams = _sort_count_list(_count_trigrams(words))[:MAX_ITEMS]
    else:
        trigrams = []

    logger.debug(
        "  %d unique_words, %d bigrams, %d trigrams, %d total words"
        % (len(unique_words), len(bigrams), len(trigrams), total_word_count)
    )

    return {
        "unique_words": unique_words,
        "bigrams": bigrams,
        "trigrams": trigrams,
        "total_word_count": total_word_count,
    }


def _create_words(text, ignore_case):
    """
    Tokenize text into words and remove standalone punctuation.

    Returns a tokenized word list.
    """
    words = re.findall(r"[\w'-]+|[.,!?;]", text, re.UNICODE)

    if ignore_case:
        words = [word.lower() for word in words]

    return [word for word in words if word not in string.punctuation]


def _sort_count_list(freq_dist):
    """
    Sort a frequency distribution by descending count.

    Returns a list of (item, count) tuples.
    """
    items = list(freq_dist.items())
    return sorted(items, key=itemgetter(1), reverse=True)


def _count_words(words, ignore_stop_words, stopwords_language):
    """
    Count word frequencies and optionally remove stop words.

    Returns the frequency distribution of words.
    """
    logger.error(stopwords_language)
    fdist = FreqDist(words)

    # remove stopwords here rather than in corpus text for speed
    if ignore_stop_words:
        logger.debug(
            "I AM IN IGNORE STOPWORDS language is {}".format(stopwords_language)
        )
        fdist = stopwords.remove_from_freq_dist(fdist, stopwords_language)

        if stopwords_language == "danish":
            # our partner advised this is necessary for Danish
            fdist = stopwords.remove_from_freq_dist(fdist, "english")

    return fdist


def _count_bigrams(words):
    """
    Count bigram frequencies from a word list.

    Returns the frequency distribution of bigrams.
    """
    bigrams = nltk.bigrams(words)
    return nltk.FreqDist(bigrams)


def _count_trigrams(words):
    """
    Count trigram frequencies from a word list.

    Returns the frequency distribution of trigrams.
    """
    trigrams = nltk.trigrams(words)
    return nltk.FreqDist(trigrams)