import datetime
import shortuuid
from pymongo import MongoClient

class MongoHandler:

	def __init__(self, app):
		uri = "mongodb://" + app.config['MONGO_HOST'] + ":" + str(app.config['MONGO_PORT'])
		self._client = MongoClient(uri)
		self._db = self._client['DataBasic']
	
	def save_document(self, collection, doc):
		uuid = shortuuid.uuid()
		self._db[collection].save({
			'doc': doc,
			'datetime': datetime.datetime.now(),
			'uuid': uuid
			})
		return uuid