import unittest, logging, time, codecs, os
import databasic.logic.wtfcsvstat as wtfcsvstat
import databasic.logic.filehandler as filehandler

class WTFCSVStatTest(unittest.TestCase):

    def setUp(self):
        self._fixtures_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),"fixtures")

    def test_get_summary_from_csv(self):
        test_data_path = os.path.join(self._fixtures_dir,'somerville-tree-details.csv')
        results = wtfcsvstat.get_summary(test_data_path)
        self.assertEqual(len(results['columns']), 43)
        self.assertEqual(results['row_count'], 13882)

    def test_get_summary_from_xls(self):
    	fixture_path = os.path.join(self._fixtures_dir,'HowAmericaInjuresItself_FromNEISS.xlsx')
        csv_file = filehandler.convert_to_csv(fixture_path)[0]
        results = wtfcsvstat.get_summary(csv_file)
        self.assertEqual(len(results['columns']), 19)
        self.assertEqual(results['row_count'], 26303)
