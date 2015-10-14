from pymongo import MongoClient

# def test():
	# mongo.test()

class MongoHandler:

	def __init__(self, host, port):
		self._client = MongoClient(host, int(port))
		print self._client

# mongo = MongoHandler(app.config['HOST'], app.config['PORT'])
