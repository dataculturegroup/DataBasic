"""
File handling utilities for DataBasic.

This module provides helpers for:
- reading files with robust encoding detection
- converting common document formats to text or CSV
- temporary file creation and cleanup
- exposing sample data references
"""

# Standard library imports (alphabetical)
import csv
import datetime
import json
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple, Union

# Third-party imports (alphabetical)
import docx2txt
import openpyxl
import requests
import xlrd
from charset_normalizer import from_bytes
from flask import Response, abort
from readability import Document
from werkzeug.utils import secure_filename
from pyth.plugins.plaintext.writer import PlaintextWriter
from pyth.plugins.rtf15.reader import Rtf15Reader

# Local imports
import databasic

# Module-level logger
logger = logging.getLogger(__name__)

# Constants
ENCODING_UTF_8 = "utf_8"
ENCODING_UTF_16 = "utf_16"
TEMP_DIR = Path(tempfile.gettempdir())
ACCEPTED_EXTENSIONS = ["txt", "docx", "rtf", "csv", "xlsx", "xls"]

# Module state (kept for compatibility)
samples: List[dict] = []
docs = None

# -------------------------
# Sample / configuration helpers
# -------------------------
def load_sample_file() -> None:
    """
    Load sample definitions from sample-data.json under the config dir.
    Updates the module-level `samples` list in place.
    """
    global samples
    samples_config_file_path = Path(databasic.get_config_dir()) / "sample-data.json"
    try:
        with samples_config_file_path.open("r", encoding="utf-8") as fh:
            samples = json.load(fh)
        logger.info("Loaded %d already-downloaded samples", len(samples))
    except FileNotFoundError:
        logger.warning("Sample config not found at %s", samples_config_file_path)
        samples = []
    except Exception:
        logger.exception("Failed to load sample config at %s", samples_config_file_path)
        samples = []

# -------------------------
# Temp file utilities
# -------------------------
def _get_temp_file(file_name_suffix: Optional[str] = None, timestamp: bool = True) -> str:
    """
    Create a unique temp file path (does not create file content).
    Returns the path as a string.
    """
    suffix = file_name_suffix or ""
    ts = time.strftime("%Y%m%d-%H%M%S") if timestamp else ""
    # Use NamedTemporaryFile to ensure uniqueness, but close immediately and return path.
    with tempfile.NamedTemporaryFile(prefix=f"{ts}-", suffix=suffix, dir=str(TEMP_DIR), delete=False) as tmp:
        tmp_path = Path(tmp.name)
    logger.debug("new tempfile at %s", tmp_path)
    return str(tmp_path)


def write_to_temp_file(text: str) -> str:
    """
    Write `text` to a new temporary file and return its path.
    """
    file_path = Path(_get_temp_file())
    logger.debug("writing %d chars to %s", len(text), file_path)
    # ensure parent dir exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    # write using utf-8
    file_path.write_text(text, encoding="utf-8")
    return str(file_path)


def write_to_csv(
    headers: Sequence[str], rows: Iterable[Sequence[object]], file_name_suffix: Optional[str] = None, timestamp: bool = True
) -> str:
    """
    Create a temporary CSV file with given headers and rows. Returns the path.
    """
    file_path = Path(_get_temp_file(file_name_suffix, timestamp))
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(list(headers))
        for row in rows:
            writer.writerow(list(row))
    return str(file_path)


def generate_csv(file_path: str) -> Response:
    """
    Return a Flask streaming Response for the CSV file at file_path.
    If file_path does not exist, abort(400).
    """
    file_path_obj = Path(file_path)
    file_name = _get_file_name(file_path)

    if not file_path_obj.is_file():
        logger.error("generate_csv: file not found %s", file_path)
        return abort(400)

    def generate():
        with file_path_obj.open("r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            for row in reader:
                yield ",".join(row) + "\n"

    headers = {"Content-Disposition": f'attachment; filename="{file_name}"'}
    return Response(generate(), headers=headers, mimetype="text/csv")


# -------------------------
# Encoding / reading helpers
# -------------------------
def open_with_correct_encoding(file_path: str) -> Tuple[str, str]:
    """
    Attempt to detect file encoding using charset_normalizer and return
    (encoding, content).

    Returns
    -------
    (encoding, content)
      - encoding: detected encoding name or ENCODING_UTF_8 as fallback
      - content: decoded text (str)
    """
    file_path_obj = Path(file_path)
    fh = file_path_obj.open("rb")
    try:
        raw_data = fh.read()
    finally:
        fh.close()

    result = from_bytes(raw_data).best()

    if result is None:
        logger.warning("Could not detect encoding for %s. Falling back to utf-8.", file_path)
        encoding = ENCODING_UTF_8
        content = raw_data.decode(encoding, errors="replace")
    else:
        encoding = result.encoding or ENCODING_UTF_8
        # charset_normalizer's best() object stringifies to decoded content
        content = str(result)

    logger.info("Detected encoding %s for file %s", encoding, file_path)
    return encoding, content


def convert_to_utf8(file_path: str) -> str:
    """
    Ensure the file content is UTF-8 encoded. If input is already UTF-8, return the
    original path. Otherwise write a UTF-8 encoded temporary file and return its path.
    """
    encoding, content = open_with_correct_encoding(file_path)
    if encoding == ENCODING_UTF_8:
        return file_path
    return write_to_temp_file(content)


# -------------------------
# Document conversions
# -------------------------
def _get_extension(file_path: str) -> str:
    """Return the normalized extension (including dot), lowercased, e.g. '.txt'."""
    return Path(file_path).suffix.lower()


def _get_file_name(file_path: str) -> str:
    return Path(file_path).name


def _docx_to_txt(file_path: str) -> str:
    """
    Convert .docx to plain text using docx2txt.
    """
    try:
        result = docx2txt.process(file_path)
        return result or ""
    except Exception:
        logger.exception("Failed to convert docx to text: %s", file_path)
        return ""


def convert_to_txt(file_path: str) -> str:
    """
    Convert various supported document types to plain text:
    .txt, .docx, .rtf, and attempt a best-effort decode for unknown extensions.

    Returns the text content as a string (never None).
    """
    logger.debug("convert_to_txt: %s", file_path)
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        logger.error("convert_to_txt: missing file %s", file_path)
        return ""

    file_size = file_path_obj.stat().st_size
    logger.debug("convert_to_txt: %d bytes at %s", file_size, file_path)

    ext = _get_extension(file_path)
    words = ""

    try:
        if ext == ".txt":
            logger.debug("loading txt file")
            _, words = open_with_correct_encoding(file_path)

        elif ext == ".docx":
            logger.debug("loading docx file")
            words = _docx_to_txt(file_path)

        elif ext == ".rtf":
            logger.debug("loading rtf file")
            try:
                with Path(file_path).open("rb") as f:
                    doc = Rtf15Reader.read(f)
                words = PlaintextWriter.write(doc).getvalue()
            except Exception:
                logger.exception("Failed to parse RTF file %s", file_path)
                words = ""

        else:
            logger.debug("unknown extension (%s); attempting best-effort decoding", ext)
            try:
                _, words = open_with_correct_encoding(file_path)
            except Exception:
                logger.exception("Wasn't able to read the words from the file %s", file_path)
                words = ""

    except Exception:
        logger.exception("Unexpected error while converting %s to text", file_path)
        words = ""

    logger.debug("loaded %d chars", len(words))
    return words


# -------------------------
# CSV conversion helpers
# -------------------------
def _open_sheet(workbook: xlrd.book.Book, index: int) -> str:
    """
    Convert an xlrd workbook sheet to a CSV temp file. Returns the path to the CSV.
    """
    sh = workbook.sheet_by_index(index)
    name = workbook.sheet_names()[index]
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)[:64]
    new_file = _get_temp_file(f"-{safe_name}.csv")
    new_path = Path(new_file)
    new_path.parent.mkdir(parents=True, exist_ok=True)
    with new_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=",", quotechar='"')
        for row_idx in range(sh.nrows):
            # convert everything to plain Python scalars
            row_values = sh.row_values(row_idx)
            writer.writerow([("" if v is None else v) for v in row_values])
    return str(new_path)


def convert_to_csv(file_path: str) -> List[str]:
    """
    Convert .xlsx and .xls workbooks to one-or-more CSV temporary files.
    For .csv returns a single-item list with the original path.
    For unsupported extensions, logs an error and returns [file_path].
    """
    ext = _get_extension(file_path)

    if ext == ".csv":
        return [file_path]

    if ext == ".xlsx":
        try:
            wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
        except Exception:
            logger.exception("Failed to open xlsx workbook: %s", file_path)
            return [file_path]

        files: List[str] = []
        for ws in wb.worksheets:
            name = ws.title or "sheet"
            safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)[:64]
            new_file = _get_temp_file(f"-{safe_name}.csv")
            new_path = Path(new_file)
            new_path.parent.mkdir(parents=True, exist_ok=True)

            with new_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=",", quotechar='"')
                for row in ws.iter_rows(values_only=True):
                    row_list = [("" if v is None else v) for v in row]
                    writer.writerow(row_list)

            files.append(str(new_path))

        return files

    if ext == ".xls":
        try:
            wb = xlrd.open_workbook(file_path)
        except Exception:
            logger.exception("Failed to open xls workbook: %s", file_path)
            return [file_path]
        files = []
        for i in range(wb.nsheets):
            files.append(_open_sheet(wb, i))
        return files

    logger.error("%s could not be converted to csv", ext)
    return [file_path]


# -------------------------
# File upload / open helpers
# -------------------------
def open_doc(doc) -> str:
    """
    Save an uploaded Werkzeug/FileStorage-like `doc` to the temp directory and return path.
    """
    filename = secure_filename(getattr(doc, "filename", "upload"))
    if not filename:
        filename = f"upload-{int(time.time())}"
    file_path = TEMP_DIR / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # doc.save may be provided by Flask's FileStorage, otherwise write from stream
    try:
        doc.save(str(file_path))
    except Exception:
        try:
            # fallback: write bytes from file-like
            stream = getattr(doc, "stream", None) or getattr(doc, "file", None)
            if stream is not None:
                with file_path.open("wb") as out_f:
                    out_f.write(stream.read())
            else:
                raise
        except Exception:
            logger.exception("Failed to save uploaded doc to %s", file_path)
            raise

    return str(file_path)


def open_docs(doc_list: Sequence) -> List[str]:
    """
    Save multiple uploaded docs and return list of paths.
    """
    file_paths: List[str] = []
    for doc in doc_list:
        file_paths.append(open_doc(doc))
    return file_paths


def delete_file(file_path: Union[str, Path]) -> None:
    """
    Remove a given file path. Silently ignore if it does not exist.
    """
    try:
        p = Path(file_path)
        if p.exists():
            p.unlink()
            logger.debug("Deleted file %s", p)
    except Exception:
        logger.exception("Failed to delete file %s", file_path)


def delete_files(file_paths: Iterable[Union[str, Path]]) -> None:
    """
    Delete multiple files. Errors for individual files are logged but do not abort.
    """
    for f in file_paths:
        delete_file(f)


def open_workbook(book) -> List[str]:
    """
    Convert an object with a `worksheets()` method into CSV temp files.
    """
    file_paths: List[str] = []
    try:
        worksheets = list(book.worksheets())
    except Exception:
        logger.exception("open_workbook expected an object with worksheets()")
        return file_paths

    for worksheet in worksheets:
        # worksheets are expected to expose title and get_all_values() to match prior behaviour
        title = getattr(worksheet, "title", "sheet")
        file_path = Path(_get_temp_file(f"-{title}.csv"))
        file_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with file_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f, delimiter=";", quotechar='"')
                values = getattr(worksheet, "get_all_values", lambda: [])()
                writer.writerows(values)
            file_paths.append(str(file_path))
        except Exception:
            logger.exception("Failed to write worksheet %s to CSV", title)
    return file_paths


# -------------------------
# Samples / lookup helpers
# -------------------------
def get_samples(tool_id: str, lang: str, domain: Optional[str] = None) -> List[Tuple[str, str]]:
    """
    Return list of matching samples as (source, title). If APP_MODE=development,
    adjust sample paths to absolute ones using databasic.get_base_dir().
    """
    matching_samples: List[Tuple[str, str]] = []

    if os.environ.get("APP_MODE") == "development":
        base_dir = databasic.get_base_dir()
        for sample in samples:
            sample["path"] = str(Path(base_dir) / sample.get("source", ""))
            logger.debug("Sample loaded at %s", sample["path"])
        logger.info("Updated sample data with base dir: %s", base_dir)

    for sample in samples:
        try:
            if tool_id in sample.get("modules", []) and lang in sample.get("lang", []):
                if (domain is None) or ("domains" not in sample) or (domain in sample.get("domains", [])):
                    if Path(sample.get("path", "")).exists():
                        matching_samples.append((sample["source"], sample.get("title", sample["source"])))
                    else:
                        logger.error("%s: file for %s doesn't exist at %s", tool_id, sample.get("source"), sample.get("path"))
        except Exception:
            logger.exception("Error while evaluating sample %s", sample)
    return matching_samples


def get_sample(source: str) -> Optional[dict]:
    """
    Return the sample dict whose 'source' contains the provided source substring.
    """
    for text in samples:
        if source in text.get("source", ""):
            return text
    return None


def get_sample_title(source: str) -> str:
    sample = get_sample(source)
    return source if sample is None else sample.get("title", source)


def get_sample_path(source: str) -> str:
    sample = get_sample(source)
    return source if sample is None else sample.get("path", source)


# -------------------------
# Utility helpers
# -------------------------
def get_file_names(file_paths: Iterable[str]) -> List[str]:
    return [Path(f).name for f in file_paths]


def generate_filename(ext: str, suffix: Optional[str], *args: str) -> str:
    """
    Generate a filename with optional args and suffix and a timestamp.
    ext: extension *with or without leading dot* (e.g. '.csv' or 'csv')
    suffix: optional suffix string (no spaces preferred)
    args: optional parts to prefix the name
    """
    clean_ext = ext.lstrip(".")
    parts = [a for a in args if a]
    prefix = "-".join(parts) + "-" if parts else ""
    suffix_part = f"{suffix}-" if suffix else ""
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{prefix}{suffix_part}{stamp}.{clean_ext}"


def download_webpage(url: str) -> dict:
    """
    Fetch a webpage and return a dict with keys 'title' and 'text' using readability.
    """
    try:
        # Headers required to avoid 403 from some sites; identify as a bot with contact info
        headers = {
            "User-Agent": "DataBasicWordCounter/1.0 (contact: rahul@databasic.io)"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        doc = Document(response.text)
        return {"title": doc.title(), "text": doc.summary()}
    except Exception:
        logger.exception("Failed to download or parse webpage %s", url)
        return {"title": "", "text": ""}
