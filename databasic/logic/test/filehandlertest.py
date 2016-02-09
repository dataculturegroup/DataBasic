import unittest, logging, time, codecs, os
import databasic.logic.filehandler as filehandler

class FileHandlerTest(unittest.TestCase):

    def setUp(self):
        self._fixtures_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),"fixtures")

    def test_write_to_temp_file(self):
        timestr = time.strftime("%Y%m%d-%H%M%S")
        data_to_write = "this is some data on %s" % timestr
        file_path = filehandler.write_to_temp_file(data_to_write)
        logging.info("Wrote to %s" % file_path)
        with codecs.open(file_path, 'r', filehandler.ENCODING_UTF_8) as f:
            data_as_written = f.read()
            self.assertEqual(data_as_written, data_to_write)

    def test_convert_to_txt_utf8(self):
        fixture_path = os.path.join(self._fixtures_dir,'utf-8.txt')
        text = filehandler.convert_to_txt(fixture_path) 
        self.assertEqual(len(text),7159)

    def test_convert_to_txt_latin1(self):
        fixture_path = os.path.join(self._fixtures_dir,'latin-1.txt')
        text = filehandler.convert_to_txt(fixture_path) 
        self.assertEqual(len(text),860)

    def test_docx_to_txt(self):
        fixture_path = os.path.join(self._fixtures_dir,'demo.docx')
        text = filehandler._docx_to_txt(fixture_path) 
        self.assertEqual(len(text),9031)
        valid_utf8 = True
        try:
            text.decode(filehandler.ENCODING_UTF_8)
        except UnicodeDecodeError:
            valid_utf8 = False
        self.assertTrue(valid_utf8)

    def test_convert_to_csv(self):
        fixture_path = os.path.join(self._fixtures_dir,'HowAmericaInjuresItself_FromNEISS.xlsx')
        results = filehandler.convert_to_csv(fixture_path)
        self.assertEqual(len(results),1)

    def test_open_with_correct_encoding(self):
        fixture_path = os.path.join(self._fixtures_dir,'latin-1.txt')
        encoding, file_handle, content = filehandler.open_with_correct_encoding(fixture_path)
        self.assertEqual(encoding,filehandler.ENCODING_LATIN_1)
        fixture_path = os.path.join(self._fixtures_dir,'utf-8.txt')
        encoding, file_handle, content = filehandler.open_with_correct_encoding(fixture_path)
        self.assertEqual(encoding,filehandler.ENCODING_UTF_8)

    def test_convert_to_utf8(self):
        fixture_path = os.path.join(self._fixtures_dir,'latin-1.txt')
        encoding, file_handle, content = filehandler.open_with_correct_encoding(fixture_path)
        self.assertEqual(encoding,filehandler.ENCODING_LATIN_1)
        temp_utf8_file_path = filehandler.convert_to_utf8(fixture_path)
        encoding, file_handle, content = filehandler.open_with_correct_encoding(temp_utf8_file_path)
        self.assertEqual(encoding,filehandler.ENCODING_UTF_8)
