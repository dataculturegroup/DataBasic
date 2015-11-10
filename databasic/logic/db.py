import datetime, json, logging, time
from pymongo import MongoClient
from bson.objectid import ObjectId
from databasic import settings

class MongoHandler:

	def __init__(self, app):
		uri = 'mongodb://' + settings.get('db', 'host') + ':' + str(settings.get('db', 'port'))
		self._client = MongoClient(uri)
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

	def save_job(self, collection, job_info):
		self._db[collection].save(job_info)

	def find_document(self, collection, doc_id):
		return self._db[collection].find_one({'_id': ObjectId(doc_id)})

	def update_document(self, collection, doc_id, update_obj):
		self._db[collection].update({'_id': ObjectId(doc_id)}, update_obj)
