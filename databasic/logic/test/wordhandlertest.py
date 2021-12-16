import unittest
import os
import databasic.logic.wordhandler as wordhandler
import databasic.logic.filehandler as filehandler


class WordHandlerTest(unittest.TestCase):

    def setUp(self):
        self._fixtures_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures")

    def test_too_many_counts(self):
        fixture_path = os.path.join(self._fixtures_dir, '22kAmazonGameReview.txt')
        words = filehandler.convert_to_txt(fixture_path)
        counts = wordhandler.get_word_counts(words, True, True, 'english')
        self.assertEqual(len(counts['unique_words']), wordhandler.MAX_ITEMS)
        self.assertEqual(len(counts['bigrams']), wordhandler.MAX_ITEMS)
        self.assertEqual(counts['total_word_count'], 2946946)


if __name__ == "__main__":
    unittest.main()
