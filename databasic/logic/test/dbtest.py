import unittest
import databasic.logic.db as db


class MongoHandlerTest(unittest.TestCase):

    def setUp(self):
        self._mongo = db.MongoHandler('localhost','databasic-test')
        self._collection = 'test'

    def test_results_for_sample(self):
        sample_id = 'test-sample-data'
        self._mongo._db[self._collection].insert_one({'sample_id': sample_id})
        existing_record = self._mongo.results_for_sample(self._collection,sample_id)
        self.assertIsNotNone(existing_record)
        missing_record = self._mongo.results_for_sample(self._collection,'not the sample data')
        self.assertIsNone(missing_record)
