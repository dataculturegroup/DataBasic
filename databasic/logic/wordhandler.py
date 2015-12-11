import nltk, re, string
from operator import itemgetter
from nltk import FreqDist
from nltk.corpus import stopwords

DEFAULT_TEXT = 'I am Sam\nSam I am\nThat Sam-I-am!\nThat Sam-I-am!\nI do not like that Sam-I-am!\nDo you like \ngreen eggs and ham?\nI do not like them, Sam-I-am.\nI do not like\ngreen eggs and ham.\nWould you like them \nhere or there?\nI would not like them\nhere or there.\nI would not like them anywhere.'

def get_word_counts(text=None, ignore_case=True, ignore_stop_words=True, stopwords_language='english'):
	text = DEFAULT_TEXT if text is None else text
	words = _create_words(text, ignore_case)
	word_count = _sort_count_list(_count_words(words, ignore_stop_words, stopwords_language))
	bigram_count = _sort_count_list(_count_bigrams(words))
	trigram_count = _sort_count_list(_count_trigrams(words))
	return [word_count, bigram_count, trigram_count]

def _create_words(text, ignore_case):
	words = re.findall(r"[\w']+|[.,!?;]", text, re.UNICODE)
	if ignore_case:
		words = [w.lower() for w in words]
	return [w for w in words if not w in string.punctuation]

def _sort_count_list(freq_dist):
	items = freq_dist.items()
	return sorted(items, key=itemgetter(1), reverse=True)

def _count_words(words, ignore_stop_words, stopwords_language):
	fdist = FreqDist(words)
	# remove stopwords here rather than in corpus text for speed
	if ignore_stop_words:
		# http://stackoverflow.com/questions/7154312/how-do-i-remove-entries-within-a-counter-object-with-a-loop-without-invoking-a-r
		for w in list(fdist):
			if w in stopwords.words(stopwords_language):
				del fdist[w]
	return fdist

def _count_bigrams(words):
	bigrams = nltk.bigrams(words)
	return nltk.FreqDist(bigrams)

def _count_trigrams(words):
	trigrams = nltk.trigrams(words)
	return nltk.FreqDist(trigrams)
