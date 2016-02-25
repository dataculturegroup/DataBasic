import unittest, logging, time, codecs, os
import databasic.logic.wordhandler as wordhandler
import databasic.logic.filehandler as filehandler

class WordHandlerTest(unittest.TestCase):

    def setUp(self):
        self._fixtures_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),"fixtures")

    def test_too_many_counts(self):
        fixture_path = os.path.join(self._fixtures_dir,'22kAmazonGameReview.txt')
        words = filehandler.convert_to_txt(fixture_path)
        counts = wordhandler.get_word_counts(words,True,True,'english')
        self.assertEqual(len(counts[0]),wordhandler.MAX_ITEMS)
        self.assertEqual(len(counts[1]),wordhandler.MAX_ITEMS)
        self.assertEqual(len(counts[2]),wordhandler.MAX_ITEMS)
