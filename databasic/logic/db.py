import datetime, json, logging, time, codecs
from pymongo import MongoClient
from bson.objectid import ObjectId

class MongoHandler:

	def __init__(self, app, host, port):
		uri = 'mongodb://' + host + ':' + str(port)
		self._client = MongoClient(uri, connect=False)
		self._db = self._client['DataBasic']
	
	def save_words(self, collection, counts, csv_files, ignore_case, ignore_stopwords, title, sample_id):
		if sample_id != '':
			sample = self._db[collection].find_one({'sample_id': str(sample_id), 'ignore_case': ignore_case, 'ignore_stopwords': ignore_stopwords})
			if sample is not None:
				return str(sample['_id'])
		return str(self._db[collection].save({
			'counts': counts,
			'csv_files': csv_files,
			'ignore_case': ignore_case,
			'ignore_stopwords': ignore_stopwords,
			'title': unicode(title),
			'sample_id': str(sample_id),
			'created_at': time.time()
			}))

	def save_csv(self, collection, results, sample_id):
		if sample_id != '':
			sample = self._db[collection].find_one({'sample_id': str(sample_id)})
			if sample is not None:
				return str(sample['_id'])
		return str(self._db[collection].save({
			'results': results,
			'sample_id': sample_id,
			'created_at': time.time()
			}))

	def save_samediff(self, collection, filenames, diff_words_doc1, diff_words_doc2, same_words, same_word_counts,
					  most_frequent_doc1, most_frequent_doc2, cosine_similarity, titles, sample_id):
		if sample_id != '':
			sample = self._db[collection].find_one({'sample_id': str(sample_id)})
			if sample is not None:
				return str(sample['_id'])
		return str(self._db[collection].save({
			'filenames': filenames,
			'diffWordsDoc1': diff_words_doc1,
			'diffWordsDoc2': diff_words_doc2,
			'sameWords': same_words,
			'sameWordCounts': same_word_counts,
			'mostFrequentDoc1': most_frequent_doc1,
			'mostFrequentDoc2': most_frequent_doc2,
			'cosineSimilarity': cosine_similarity,
			'titles': titles,
			'sample_id': sample_id
			}))

	def save_job(self, collection, job_info):
		self._db[collection].save(job_info)

	def find_document(self, collection, doc_id):
		return self._db[collection].find_one({'_id': ObjectId(doc_id)})

	def update_document(self, collection, doc_id, update_obj):
		self._db[collection].update({'_id': ObjectId(doc_id)}, update_obj, upsert=True)
