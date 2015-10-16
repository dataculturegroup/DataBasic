import datetime
import shortuuid
from pymongo import MongoClient

class MongoHandler:

	def __init__(self, app):
		uri = "mongodb://" + app.config['MONGO_HOST'] + ":" + str(app.config['MONGO_PORT'])
		self._client = MongoClient(uri)
		self._db = self._client['DataBasic']
	
	def save_words(self, collection, doc, ignore_case, ignore_stopwords):
		uuid = shortuuid.uuid()
		self._db[collection].save({
			'doc': doc,
			'ignore_case': ignore_case,
			'ignore_stopwords': ignore_stopwords,
			'datetime': datetime.datetime.now(),
			'uuid': uuid
			})
		return uuid

	def save_csv(self, collection, results):
		uuid = shortuuid.uuid()
		self._db[collection].save({
			'results': results,
			'datetime': datetime.datetime.now(),
			'uuid': uuid
			})
		return uuid

	def get_document(self, collection, uuid):
		return self._db[collection].find({'uuid': uuid})[0]