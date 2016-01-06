import unittest, logging, time, codecs, os
import databasic.logic.wtfcsvstat as wtfcsvstat

class WTFCSVStatTest(unittest.TestCase):

    def setUp(self):
        self._fixtures_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),"fixtures")

    def test_get_summary(self):
        test_data_path = os.path.join(self._fixtures_dir,'somerville-tree-details.csv')
        results = wtfcsvstat.get_summary(test_data_path)
        self.assertEqual(len(results['columns']), 43)
        self.assertEqual(results['row_count'], 13882)
