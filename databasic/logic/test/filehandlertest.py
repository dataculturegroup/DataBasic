"""
Unit tests for databasic.logic.filehandler.

These tests validate:
- reading files with encoding detection
- converting documents to text
- converting spreadsheets to CSV files
- creating and deleting temporary files
- streaming CSV downloads via Flask Response
- saving uploaded files to the temp directory
- downloading and extracting webpage text via readability (with mocked HTTP)
"""

from __future__ import annotations

import io
import unittest
from pathlib import Path
from typing import List
from unittest.mock import Mock, patch

from flask import Flask
from werkzeug.datastructures import FileStorage

import openpyxl

import databasic.logic.filehandler as filehandler

class FileHandlerTest(unittest.TestCase):
    """Tests for filehandler helpers."""

    def setUp(self) -> None:
        self._fixtures_dir = Path(__file__).resolve().parent / "fixtures"
        self._created_files: List[str] = []

        # Minimal Flask app for Response/app_context usage.
        self._app = Flask(__name__)

    def tearDown(self) -> None:
        filehandler.delete_files(self._created_files)

    def _track(self, path: str) -> str:
        """Track a file for deletion in tearDown."""
        self._created_files.append(path)
        return path

    @staticmethod
    def _is_utf8_label(label: str) -> bool:
        """
        charset-normalizer may return labels like 'utf_8', 'utf_8_sig', 'UTF-8'.
        Treat all of these as UTF-8.
        """
        if not label:
            return False
        normalized = label.replace("-", "_").lower()
        return normalized.startswith("utf_8")

    @staticmethod
    def _is_utf16_label(label: str) -> bool:
        """
        charset-normalizer may return labels like 'utf_16', 'utf_16_le', 'UTF-16LE'.
        Treat all of these as UTF-16.
        """
        if not label:
            return False
        normalized = label.replace("-", "_").lower()
        return normalized.startswith("utf_16")

    def test_write_to_temp_file_roundtrip(self) -> None:
        """write_to_temp_file writes text to a temp file and returns the path."""
        data_to_write = "this is some data"
        file_path = self._track(filehandler.write_to_temp_file(data_to_write))

        read_back = Path(file_path).read_text(encoding="utf-8")
        self.assertEqual(read_back, data_to_write)

    def test_convert_to_txt_reads_utf8_fixture(self) -> None:
        """convert_to_txt reads a UTF-8 fixture and returns expected length."""
        fixture_path = self._fixtures_dir / "utf-8.txt"
        text = filehandler.convert_to_txt(str(fixture_path))
        self.assertEqual(len(text), 7159)

    def test_convert_to_txt_reads_latin1_fixture(self) -> None:
        """convert_to_txt reads a Latin-1/Windows-1252-like fixture and returns expected length."""
        fixture_path = self._fixtures_dir / "latin-1.txt"
        text = filehandler.convert_to_txt(str(fixture_path))
        self.assertEqual(len(text), 860)

    def test_docx_to_txt_fixture_is_utf8_encodable(self) -> None:
        """_docx_to_txt returns text that can be encoded as UTF-8."""
        fixture_path = self._fixtures_dir / "demo.docx"
        text = filehandler._docx_to_txt(str(fixture_path))

        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 0)
        text.encode("utf-8")  # should not raise

    def test_convert_to_csv_xlsx_fixture_produces_csv_files(self) -> None:
        """convert_to_csv converts an XLSX fixture to one or more CSV files."""
        fixture_path = self._fixtures_dir / "HowAmericaInjuresItself_FromNEISS.xlsx"
        results = filehandler.convert_to_csv(str(fixture_path))

        self.assertEqual(len(results), 1)
        self.assertTrue(Path(results[0]).exists())
        self._track(results[0])

    def test_open_with_correct_encoding_detects_utf8_and_utf16(self) -> None:
        """open_with_correct_encoding detects encodings and returns decoded content."""
        utf8_path = self._fixtures_dir / "utf-8.txt"
        encoding, content = filehandler.open_with_correct_encoding(str(utf8_path))
        self.assertTrue(self._is_utf8_label(encoding), msg=f"Unexpected utf8 encoding label: {encoding}")
        self.assertGreater(len(content), 0)

        utf16_path = self._fixtures_dir / "utf-16.txt"
        encoding, content = filehandler.open_with_correct_encoding(str(utf16_path))
        self.assertTrue(self._is_utf16_label(encoding), msg=f"Unexpected utf16 encoding label: {encoding}")
        self.assertGreater(len(content), 0)

    def test_convert_to_utf8_creates_utf8_temp_file_when_needed(self) -> None:
        """convert_to_utf8 creates a UTF-8 temp file when the input is not UTF-8."""
        fixture_path = self._fixtures_dir / "macroman.txt"
        enc_before, content_before = filehandler.open_with_correct_encoding(str(fixture_path))

        self.assertFalse(self._is_utf8_label(enc_before), msg=f"Fixture unexpectedly detected as UTF-8: {enc_before}")
        self.assertGreater(len(content_before), 0)

        temp_utf8_file_path = self._track(filehandler.convert_to_utf8(str(fixture_path)))
        self.assertNotEqual(temp_utf8_file_path, str(fixture_path))

        enc_after, content_after = filehandler.open_with_correct_encoding(temp_utf8_file_path)
        self.assertTrue(self._is_utf8_label(enc_after), msg=f"Converted file not detected as UTF-8: {enc_after}")
        self.assertGreater(len(content_after), 0)

    def test_write_to_csv_and_generate_csv_streams_content(self) -> None:
        """write_to_csv creates a CSV file and generate_csv streams it in a Flask Response."""
        headers = ["a", "b"]
        rows = [[1, 2], [3, 4]]

        csv_path = self._track(filehandler.write_to_csv(headers, rows, file_name_suffix="-test.csv", timestamp=False))
        self.assertTrue(Path(csv_path).exists())

        with self._app.app_context():
            resp = filehandler.generate_csv(csv_path)

            self.assertEqual(resp.mimetype, "text/csv")
            self.assertIn("Content-Disposition", resp.headers)

            body = "".join(chunk for chunk in resp.response)  # generator yields strings
            self.assertIn("a,b\n", body)
            self.assertIn("1,2\n", body)
            self.assertIn("3,4\n", body)

    def test_generate_csv_missing_file_raises_http_exception(self) -> None:
        """generate_csv aborts with 400 when the file does not exist."""
        missing = str(Path(filehandler.TEMP_DIR) / "definitely-does-not-exist.csv")

        with self._app.app_context():
            with self.assertRaises(Exception):
                filehandler.generate_csv(missing)

    def test_convert_to_txt_missing_file_returns_empty_string(self) -> None:
        """convert_to_txt returns an empty string when the file path does not exist."""
        missing = str(Path(filehandler.TEMP_DIR) / "nope.txt")
        text = filehandler.convert_to_txt(missing)
        self.assertEqual(text, "")

    def test_convert_to_txt_reads_rtf_file(self) -> None:
        """convert_to_txt extracts text from an RTF file."""
        rtf_payload = r"{\rtf1\ansi This is {\b bold} text.}"
        rtf_path = Path(self._track(filehandler._get_temp_file("-test.rtf", timestamp=False)))
        rtf_path.write_bytes(rtf_payload.encode("ascii"))

        text = filehandler.convert_to_txt(str(rtf_path))
        self.assertIn("This is", text)
        self.assertIn("bold", text)
        self.assertIn("text.", text)

    def test_convert_to_csv_passthrough_for_csv_input(self) -> None:
        """convert_to_csv returns [file_path] when the input is already a CSV."""
        csv_path = self._track(
            filehandler.write_to_csv(["x"], [[1]], file_name_suffix="-passthrough.csv", timestamp=False)
        )
        results = filehandler.convert_to_csv(csv_path)
        self.assertEqual(results, [csv_path])

    def test_convert_to_csv_xlsx_multiple_sheets_creates_multiple_csv_files(self) -> None:
        """convert_to_csv creates one CSV file per sheet for a multi-sheet XLSX workbook."""
        xlsx_path = Path(self._track(filehandler._get_temp_file("-multi.xlsx", timestamp=False)))

        wb = openpyxl.Workbook()
        ws1 = wb.active
        ws1.title = "Sheet One"
        ws1.append(["h1", "h2"])
        ws1.append([1, 2])

        ws2 = wb.create_sheet("Second Sheet")
        ws2.append(["a", "b"])
        ws2.append(["x", "y"])

        wb.save(xlsx_path)

        results = filehandler.convert_to_csv(str(xlsx_path))
        self.assertEqual(len(results), 2)

        for p in results:
            self.assertTrue(Path(p).exists())
            self._track(p)

        csv_text = Path(results[0]).read_text(encoding="utf-8")
        self.assertTrue(("h1,h2" in csv_text) or ("a,b" in csv_text))

    def test_convert_to_csv_unsupported_extension_returns_original_path(self) -> None:
        """convert_to_csv returns [file_path] for unsupported extensions."""
        temp_txt = self._track(filehandler.write_to_temp_file("hello"))
        new_path = Path(temp_txt).with_suffix(".bin")

        Path(temp_txt).rename(new_path)
        self._created_files.remove(temp_txt)
        self._track(str(new_path))

        results = filehandler.convert_to_csv(str(new_path))
        self.assertEqual(results, [str(new_path)])

    def test_delete_file_missing_path_is_noop(self) -> None:
        """delete_file does not raise when the file does not exist."""
        missing = str(Path(filehandler.TEMP_DIR) / "missing-delete-file.txt")
        filehandler.delete_file(missing)

    def test_open_doc_saves_filestorage_and_sanitizes_filename(self) -> None:
        """open_doc saves an uploaded FileStorage to TEMP_DIR and sanitizes the filename."""
        payload = b"hello world"
        storage = FileStorage(
            stream=io.BytesIO(payload),
            filename="../evil name.txt",
            content_type="text/plain",
        )

        saved_path = self._track(filehandler.open_doc(storage))
        saved = Path(saved_path)

        self.assertTrue(saved.exists())
        self.assertEqual(saved.read_bytes(), payload)
        self.assertNotIn("..", saved.name)

    @patch("databasic.logic.filehandler.requests.get")
    def test_download_webpage_success_and_failure(self, mock_get: Mock) -> None:
        """download_webpage returns extracted title/text on success and empty values on failure."""
        ok_resp = Mock()
        ok_resp.text = "<html><head><title>T</title></head><body><p>Hello</p></body></html>"
        ok_resp.raise_for_status = Mock()
        mock_get.return_value = ok_resp

        result = filehandler.download_webpage("https://example.com")
        self.assertIn("title", result)
        self.assertIn("text", result)
        self.assertIsInstance(result["title"], str)
        self.assertIsInstance(result["text"], str)

        mock_get.side_effect = RuntimeError("boom")
        result = filehandler.download_webpage("https://example.com")
        self.assertEqual(result, {"title": "", "text": ""})


if __name__ == "__main__":
    unittest.main()