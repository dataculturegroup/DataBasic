import requests
from newspaper import Article
import os, datetime, time, tempfile, json, xlrd, logging
from pyth.plugins.rtf15.reader import Rtf15Reader
from pyth.plugins.plaintext.writer import PlaintextWriter
from flask import Response, abort
import csv
import docx2txt
from werkzeug.utils import secure_filename
from bs4 import UnicodeDammit

import databasic

logger = logging.getLogger(__name__)

ENCODING_UTF_8 = 'utf-8'
ENCODING_UTF_16 = 'utf-16'
ENCODING_LATIN_1 = 'latin-1'
TEMP_DIR = tempfile.gettempdir()

samples = []
docs = None
ACCEPTED_EXTENSIONS = ['txt', 'docx', 'rtf', 'csv', 'xlsx', 'xls']


def load_sample_file():
    global samples
    samples_config_file_path = os.path.join(databasic.get_config_dir(), 'sample-data.json')
    samples = json.load(open(samples_config_file_path))
    logger.info("Loaded {} already-downloaded samples".format(len(samples)))


def write_to_temp_file(text):
    file_path = _get_temp_file()
    logger.debug("writing %d chars to %s" % (len(text), file_path))
    tmp_file = open(file_path, 'w')
    tmp_file.write(text)
    tmp_file.close()
    return file_path


def write_to_csv(headers, rows, file_name_suffix=None, timestamp=True):
    file_path = _get_temp_file(file_name_suffix, timestamp)
    with open(file_path, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)
    return file_path


def generate_csv(file_path):
    file_name = _get_file_name(file_path)
    if not os.path.isfile(file_path):
        return abort(400)

    def generate():
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                yield ','.join(row) + '\n'

    return Response(generate(), headers={'Content-Disposition': 'attachment;filename='+file_name}, mimetype='text/csv')


def convert_to_txt(file_path):
    logger.debug("convert_to_txt: %s" % file_path)
    if not os.path.exists(file_path):
        logger.error("missing file %s", file_path)
    file_size = os.stat(file_path).st_size
    logger.debug("convert_to_txt: %d bytes at %s", file_size, file_path)
    ext = _get_extension(file_path)
    if ext == '.txt':
        logger.debug("loading txt file")

        #CSD replacing with default open bc txt files are getting converted weirdly
        with open(file_path, 'r') as myfile:
            words = myfile.read()
        #try:
        #    encoding, file_handle, words = open_with_correct_encoding(file_path)
        #except Exception:
        #    logger.error("Wasn't able to read the words from the file %s" % file_path)
        #    words = ""
    elif ext == '.docx':
        logger.debug("loading docx file")
        words = _docx_to_txt(file_path)
    elif ext == '.rtf':
        logger.debug("loading rtf file")
        doc = Rtf15Reader.read(open(file_path))
        words = PlaintextWriter.write(doc).getvalue()
    else:
        logging.warning("Couldn't find an extension on the file, so assuming text")
        with open(file_path, 'r') as myfile:
            words = myfile.read()
    logger.debug("loaded %d chars" % len(words))
    return words


def convert_to_utf8(file_path):
    encoding, file_handle, content = open_with_correct_encoding(file_path)
    if encoding is ENCODING_UTF_8:
        return file_path
    # now we have to save it as utf8
    return write_to_temp_file(content)


def open_with_correct_encoding(file_path):
    """
    Since you can't actually detect the encoding of a file perfectly, default to utf-8
    and fallback to any others we want.  This returns the file handle, and the content, since 
    you have to try to read the file for it to fail on a content encoding error.
    """
    file_handle = open(file_path, 'r')
    content = file_handle.read()
    dammit = UnicodeDammit(content)
    file_handle.seek(0)
    return [dammit.original_encoding, file_handle, content]


def convert_to_csv(file_path):
    ext = _get_extension(file_path)
    if ext == '.csv':
        return [file_path]
    elif ext == '.xlsx' or ext == '.xls':
        wb = xlrd.open_workbook(file_path)
        files = []
        for i in range(wb.nsheets):
            files.append(_open_sheet(wb, i))
        return files
    logger.error(ext + ' could not be converted to csv')
    return [file_path]


def open_doc(doc):
    filename = secure_filename(doc.filename)
    file_path = os.path.join(TEMP_DIR, filename)
    doc.save(file_path)
    return file_path


def open_docs(doc_list):
    file_paths = []
    for doc in doc_list:
        file_paths.append(open_doc(doc))
    return file_paths


def delete_files(file_paths):
    for f in file_paths:
        delete_file(f)


def delete_file(file_path):
    os.remove(file_path)


def open_workbook(book):
    file_paths = []
    for i, worksheet in enumerate(book.worksheets()):
        file_path = _get_temp_file('-' + worksheet.title + '.csv')
        with open(file_path, 'wb') as f:
            writer = csv.writer(f, delimiter=str(';'), quotechar=str('"'))
            writer.writerows(worksheet.get_all_values())
        file_paths.append(file_path)
    return file_paths


def get_samples(tool_id, lang, domain=None):
    matching_samples = []
    if os.environ.get('APP_MODE', None) == "development":
        base_dir = databasic.get_base_dir()
        # change the paths to absolute ones
        for sample in samples:
            sample['path'] = os.path.join(base_dir, sample['source'])
            logger.debug("Sample loaded at %s", os.path.join(base_dir, sample['source']))
        logger.info("  Updated sample data with base dir: {}".format(base_dir))

    for sample in samples:
        if tool_id in sample['modules'] and lang in sample['lang']:  # filter samples by language and tool
            if (domain is None) or ('domains' not in sample) or (domain in sample['domains']): # filter by domain (if specified)
                if os.path.exists(sample['path']):

                    # only include samples we have been able to download from the static sample server URL
                    matching_samples.append((sample['source'], sample['title']))
                else:
                    logger.error("%s: file for %s doesn't exist at %s", tool_id, sample['source'], sample['path'])
    return matching_samples


def get_sample(source):
    for text in samples:
        if source in text['source']:
            return text
    return None


def get_sample_title(source):
    sample = get_sample(source)
    return source if sample is None else sample['title']


def get_sample_path(source):
    sample = get_sample(source)
    return source if sample is None else sample['path']


def get_file_names(file_paths):
    file_names = []
    for f in file_paths:
        file_names.append(_get_file_name(f))
    return file_names


def generate_filename(ext, suffix, *args):
    files = '-'.join(args) + '-' if len(args) > 0 else ''
    suffix = suffix + '-' if suffix is not None and suffix != '' else ''
    suffix = suffix.replace(' ', '-')
    ext = ext[1:] if '.' in ext[0] else ext
    return files + suffix + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + '.' + ext


def download_webpage(url):
    article = Article(url)
    article.download()
    article.parse()
    return {'title': article.title, 'text': article.text}


def _open_sheet(workbook, index):
    sh = workbook.sheet_by_index(index)
    name = workbook.sheet_names()[index]
    new_file = _get_temp_file('-' + name + '.csv')
    with open(new_file, 'w') as f:
        writer = csv.writer(f, delimiter=str(','), quotechar=str('"'))
        for row in range(sh.nrows):
            writer.writerow(sh.row_values(row))
    return new_file


def _get_file_name(file_path):
    return os.path.split(file_path)[1]


def _get_temp_file(file_name_suffix=None, timestamp=True):
    file_name = ''
    if timestamp:
        file_name = time.strftime("%Y%m%d-%H%M%S")
    if file_name_suffix is not None:
        file_name += file_name_suffix
    file_path = os.path.join(TEMP_DIR, file_name)
    logger.debug("new tempfile at %s", file_path)
    return file_path


def _get_extension(file_path):
    return os.path.splitext(file_path)[1]


def _docx_to_txt(file_path):
    return docx2txt.process(file_path)
