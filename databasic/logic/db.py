import datetime
import logging
import time
import pytz
from pymongo import MongoClient
from bson.objectid import ObjectId

EXPIRE_AFTER = 60  # time in days
logger = logging.getLogger(__name__)


class MongoHandler:

    def __init__(self, uri, db_name):
        logger.info("Connected to '{}' Mongo collection at {}".format(db_name, uri))
        self._client = MongoClient(uri, connect=False)
        self._db = self._client[db_name]

    def save_words(self, collection, counts, ignore_case, ignore_stopwords, title, sample_id, source, extras=None):
        data_to_save = extras if extras is not None else {}
        data_to_save.update({
            'counts': counts,
            'ignore_case': ignore_case,
            'ignore_stopwords': ignore_stopwords,
            'title': title,
            'sample_id': str(sample_id),
            'source': source,
            'created_at': time.time(),
            })
        result = self._db[collection].insert_one(data_to_save)
        return str(result.inserted_id)

    def results_for_sample(self, collection, sample_id):
        logger.debug("checking for sample %s", sample_id)
        sample = self._db[collection].find_one({'sample_id': str(sample_id)})

        if sample is not None:
            return str(sample['_id'])

    def save_csv(self, collection, results, sample_id, source):
        result = self._db[collection].insert_one({
            'results': results,
            'sample_id': str(sample_id),
            'source': source,
            'created_at': time.time()
            })
        return str(result.inserted_id)

    def save_samediff(self, collection, filenames, total_words_doc1, total_words_doc2, diff_words_doc1, diff_words_doc2,
                      same_words, same_word_counts, most_frequent_doc1, most_frequent_doc2, cosine_similarity, titles,
                      sample_id, source):
        result = self._db[collection].insert_one({
            'filenames': filenames,
            'totalWordsDoc1': total_words_doc1,
            'totalWordsDoc2': total_words_doc2,
            'diffWordsDoc1': diff_words_doc1,
            'diffWordsDoc2': diff_words_doc2,
            'sameWords': same_words,
            'sameWordCounts': same_word_counts,
            'mostFrequentDoc1': most_frequent_doc1,
            'mostFrequentDoc2': most_frequent_doc2,
            'cosineSimilarity': cosine_similarity,
            'titles': titles,
            'sample_id': str(sample_id),
            'source': source,
            'created_at': time.time()
            })
        return str(result.inserted_id)


    def save_job(self, collection, job_info):
        self._db[collection].insert_one(job_info)

    def find_document(self, collection, doc_id):
        logger.debug("trying to find one doc with ID %s", doc_id)
        return self._db[collection].find_one({'_id': ObjectId(doc_id)})

    def get_remaining_days(self, collection, doc_id):
        doc = self.find_document(collection, doc_id)['_id']
        now = datetime.datetime.now(pytz.utc)
        age = now-doc.generation_time
        remaining = datetime.timedelta(days=EXPIRE_AFTER)-age
        return remaining.days+1

    def remove_all_sample_data(self):
        self.remove_sample_data('wordcounter')
        self.remove_sample_data('wtfcsv')
        self.remove_sample_data('samediff')
        self.remove_sample_data('connectthedots')
        logger.debug("Removed all sample data")

    def remove_sample_data(self, collection):
        self._db[collection].delete_many({'sample_id': {'$exists': True, '$ne': ''}})

    def remove_expired_results(self, collection):
        limit = datetime.datetime.now(pytz.utc) - datetime.timedelta(days=EXPIRE_AFTER)
        _id = ObjectId.from_datetime(limit)
        docs = self._db[collection].find({'_id': {'$lt': _id}, 'sample_id': ''})
        for d in docs:
            if 'title' in d:
                logger.info(collection + ': removing ' + d['title'])
            else:
                logger.info(collection + ': removing (no name)')
        self._db[collection].delete_many({'_id': {'$lt': _id}, 'sample_id': ''})

    def remove_all_expired_results(self):
        self.remove_expired_results('wordcounter')
        self.remove_expired_results('wtfcsv')
        self.remove_expired_results('samediff')
        self.remove_expired_results('connectthedots')

    def remove_by_id(self, collection, id):
        return self._db[collection].delete_one({'_id': ObjectId(id)})
