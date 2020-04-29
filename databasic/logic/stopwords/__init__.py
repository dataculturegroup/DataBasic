import os
from nltk.corpus import stopwords
import logging

from databasic import get_base_dir

logger = logging.getLogger(__name__)

language2stopwords = {}  # cache of language name to our custom stopwords list


def remove_from_freq_dist(fdist, language):
    # http://stackoverflow.com/questions/7154312/how-do-i-remove-entries-within-a-counter-object-with-a-loop-without-invoking-a-r
    num_removed = 0
    custom_stopwords = _custom_stopwords_list(language)
    # logger.debug(",".join(custom_stopwords))
    for w in list(fdist):
        # logger.debug("    checking {}".format(w))
        if (w in stopwords.words(language)) or (w in custom_stopwords):
            num_removed += 1
            del fdist[w]
    logger.debug("  removed {} stopwords".format(num_removed))
    return fdist


def _custom_stopwords_list(language, force=True):
    """
    We have some extra stopwords that we want to use in some of our languages
    :param language: NLTK-compatible name of language
    :return: a list of stopwords we added for that language, [] if none to add
    """
    if force or (language not in language2stopwords):
        path_to_file = os.path.join(get_base_dir(), 'databasic', 'logic', 'stopwords', language)
        try:
            f = open(path_to_file, 'r')
            custom_stopwords = [w.strip() for w in f.readlines() if len(w.strip()) > 0]
            # logger.debug("Loaded {} custom {} stopwords".format(len(custom_stopwords), language))
            f.close()
        except OSError:
            custom_stopwords = []
        language2stopwords[language] = custom_stopwords
    # speed things up by caching the stopword lists in memory, so it isn't file I/O bound
    return language2stopwords[language]
