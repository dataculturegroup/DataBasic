import datetime, json, logging, time, codecs
from pymongo import MongoClient
from bson.objectid import ObjectId
from databasic import settings

class MongoHandler:

	def __init__(self, app):
		uri = 'mongodb://' + settings.get('db', 'host') + ':' + str(settings.get('db', 'port'))
		self._client = MongoClient(uri, connect=False)
		self._db = self._client['DataBasic']
	
	def save_words(self, collection, counts, csv_files, ignore_case, ignore_stopwords, title):
		return str(self._db[collection].save({
			'counts': counts,
			'csv_files': csv_files,
			'ignore_case': ignore_case,
			'ignore_stopwords': ignore_stopwords,
			'title': str(title),
			'created_at': time.time()
			}))

	def save_csv(self, collection, results):
		return str(self._db[collection].save({
			'results': results,
			'created_at': time.time()
			}))

	# deprecate(?)
	def save_queued_files(self, collection, filepaths, filenames, is_sample_data, email, results_url_base):
		properties = {
			'filepaths': filepaths,
			'filenames': filenames,
			'is_sample_data': is_sample_data,
			'email': email,
			'status': 'queued',
			'created_at': time.time()
			}
		logging.info(json.dumps(properties))
		doc_id = str(self._db[collection].save(properties))
		self.update_document(collection, doc_id, {'$set': {'results_url': results_url_base + doc_id}})
		return doc_id

	def save_samediff(self, collection, filenames, diff_words_doc1, diff_words_doc2, same_words, same_word_counts,
					  most_frequent_doc1, most_frequent_doc2, cosine_similarity, titles):
		return str(self._db[collection].save({
			'filenames': filenames,
			'diffWordsDoc1': diff_words_doc1,
			'diffWordsDoc2': diff_words_doc2,
			'sameWords': same_words,
			'sameWordCounts': same_word_counts,
			'mostFrequentDoc1': most_frequent_doc1,
			'mostFrequentDoc2': most_frequent_doc2,
			'cosineSimilarity': cosine_similarity,
			'titles': titles
			}))

	def save_job(self, collection, job_info):
		self._db[collection].save(job_info)

	def find_document(self, collection, doc_id):
		return self._db[collection].find_one({'_id': ObjectId(doc_id)})

	def update_document(self, collection, doc_id, update_obj):
		self._db[collection].update({'_id': ObjectId(doc_id)}, update_obj, upsert=True)
