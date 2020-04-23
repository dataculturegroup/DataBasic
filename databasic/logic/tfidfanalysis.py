import os
import codecs, re, time, string, logging, math
from operator import itemgetter
from nltk import FreqDist
from nltk.corpus import stopwords
import textmining
from scipy import spatial
from . import filehandler

def most_frequent_terms(*args):
    tdm = textmining.TermDocumentMatrix(simple_tokenize_remove_our_stopwords)
    for doc in args:
        tdm.add_doc(doc)

    freqs = []
    for d in tdm.sparse:
        f = [(freq, name) for (name, freq) in list(d.items())]
        f.sort(reverse=True)
        freqs.append(f)
    
    return freqs

def doc_to_words(document):
    '''
    Turn a document into a list of all the words in it
    # TODO: include word stemming
    '''
    t1 = time.time()
    words = re.findall(r"[\w']+|[.,!?;]", document, re.UNICODE)
    t2 = time.time()
    words = [w.lower() for w in words]
    t3 = time.time()
    words = [w for w in words if not w in string.punctuation]
    t4 = time.time()
    logging.debug("   tokenize: %d" % (t2-t1))
    logging.debug("   ignore_case: %d" % (t3-t2))
    logging.debug("   remove punctuation: %d" % (t4-t3))
    return words

# TODO add a langauge param to remove spanish stop words too
def term_frequency(words):
    '''
    Turn a list of words into a NLTK frequency distribution object
    '''
    t1 = time.time()
    fdist = FreqDist(words)
    # remove stopwords here rather than in corpus text for speed
    # http://stackoverflow.com/questions/7154312/how-do-i-remove-entries-within-a-counter-object-with-a-loop-without-invoking-a-r
    for w in list(fdist):
        if w in stopwords.words('english'):
            del fdist[w]
    t2 = time.time()
    logging.debug("   create term freq: %d" % (t2-t1))
    return fdist
    
def _count_incidence(lookup, term):
    if term in lookup:
        lookup[term] += 1
    else:
        lookup[term] = 1

def inverse_document_frequency(list_of_fdist_objects):
    '''
    Turn a list of words lists into a document frequency
    '''
    doc_count = len(list_of_fdist_objects)
    term_doc_incidence = {}
    t1 = time.time()
    [_count_incidence(term_doc_incidence,term) \
            for fdist in list_of_fdist_objects \
            for term in list(fdist.keys()) ]
    t2 = time.time()
    idf = { term: math.log(float(doc_count)/float(incidence)) for term, incidence in term_doc_incidence.items() }
    t3 = time.time()
    logging.debug("   create df: %d" % (t2-t1))
    logging.debug("   create idf: %d" % (t3-t2))
    return idf
    
def tf_idf(list_of_file_paths):
    '''
    Compute and return tf-idf from a list of file paths (sorted by tfidf desc)
    '''
    doc_list = [ filehandler.convert_to_txt(file_path) for file_path in list_of_file_paths ]
    tf_list = [ term_frequency( doc_to_words(doc) ) for doc in doc_list ]   # a list of FreqDist objects
    idf = inverse_document_frequency(tf_list)
    tf_idf_list = [ [{'term':term, 'tfidf':frequency*idf[term], 'frequency': frequency} for term, frequency in tf.items()] for tf in tf_list ]
    tf_idf_list = [ sorted(tf_idf, key=itemgetter('tfidf'), reverse=True)  for tf_idf in tf_idf_list ]
    return tf_idf_list

def simple_tokenize_remove_our_stopwords(document):
    """
    Clean up a document and split into a list of words, removing stopwords.

    Converts document (a string) to lowercase and strips out everything
    which is not a lowercase letter. Then removes stopwords.

    """
    document = document.lower()
    document = re.sub('[^a-z\']', ' ', document)
    words = document.strip().split()
    # Remove stopwords
    words = [word for word in words if word not in stopwords.words('english')]
    return words

def cosine_similarity(list_of_file_paths):
    # Create some very short sample documents
    doc_list = [ filehandler.convert_to_txt(file_path) for file_path in list_of_file_paths ]
    # Initialize class to create term-document matrix
    tdm = textmining.TermDocumentMatrix(tokenizer=simple_tokenize_remove_our_stopwords)
    for doc in doc_list:
        tdm.add_doc(doc)
    results = []
    is_first_row1 = True
    for row1 in tdm.rows(cutoff=1):
        if is_first_row1:
            is_first_row1 = False
            continue
        is_first_row2 = True
        cols = []
        for row2 in tdm.rows(cutoff=1):
            if is_first_row2:
                is_first_row2 = False
                continue
            cols.append( 1 - spatial.distance.cosine(row1,row2) )
        results.append(cols)
    return results