import tempfile
from urllib2 import urlopen
from goose import Goose
import os, datetime, time, tempfile, codecs, unicodecsv, json, xlrd, logging
from pyth.plugins.rtf15.reader import Rtf15Reader
from pyth.plugins.plaintext.writer import PlaintextWriter
from flask import Response, abort
from flask.ext.uploads import UploadSet, configure_uploads, TEXT, patch_request_class, UploadNotAllowed
import textract
import databasic

logger = logging.getLogger(__name__)

ENCODING_UTF_8 = 'utf-8'
ENCODING_UTF_16 = 'utf-16'
ENCODING_LATIN_1 = 'latin-1'
TEMP_DIR = tempfile.gettempdir()

samples = []
docs = None

def init_uploads():
    global docs
    global TEMP_DIR
    logger.info("Uploads will be written to %s", TEMP_DIR)
    databasic.app.config['UPLOADED_DOCS_DEST'] = TEMP_DIR
    docs = UploadSet(name='docs', extensions=('txt', 'docx', 'rtf', 'csv', 'xlsx', 'xls'))
    configure_uploads(databasic.app, (docs))
    #patch_request_class(databasic.app, 10 * 1024 * 1024) # 100MB

def init_samples():
    global samples
    samples_config_file_path = os.path.join(databasic.get_config_dir(),'sample-data.json')
    samples = json.load(open(samples_config_file_path))
    if databasic.app.config.get(databasic.ENV_APP_MODE) == databasic.APP_MODE_DEV:
        # change the paths to absolute ones
        for sample in samples:
            sample['path'] = os.path.join(databasic.get_base_dir(),sample['source'])
        logger.info("Updated sample data with base dir: %s" % databasic.get_base_dir())
    else:
        # copy from server to local temp dir and change to abs paths (to temp dir files)
        url_base = databasic.app.config.get('SAMPLE_DATA_SERVER')
        for sample in samples:
            url = url_base+sample['source']
            text = urlopen(url).read()
            f = tempfile.NamedTemporaryFile(delete=False)
            f.write(text)
            f.close()
            sample['path'] = f.name
        logger.info("Downloaded sample data and saved to tempdir")
    for sample in samples:
        file_size = os.stat(sample['path']).st_size
        logger.debug("  Cached %d bytes of %s to %s", file_size, sample['source'], sample['path'])

def write_to_temp_file(text):
    file_path = _get_temp_file()
    logger.debug("writing %d chars to %s" % (len(text),file_path))
    file = codecs.open(file_path, 'w', ENCODING_UTF_8)
    file.write(text)
    file.close()
    return file_path

def write_to_csv(headers, rows, file_name_suffix=None, timestamp=True):
    file_path = _get_temp_file(file_name_suffix, timestamp)
    with open(file_path, 'w') as f:
        writer = unicodecsv.writer(f, encoding=ENCODING_UTF_8)
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
            reader = unicodecsv.reader(f, encoding=ENCODING_UTF_8)
            for row in reader:
                yield ','.join(row) + '\n'
    return Response(generate(), headers={'Content-Disposition':'attachment;filename='+file_name},mimetype='text/csv')

def convert_to_txt(file_path):
    logger.debug("convert_to_txt: %s" % file_path)
    words = None
    if not os.path.exists(file_path):
        logger.error("missing file %s", file_path)
    file_size = os.stat(file_path).st_size
    logger.debug("convert_to_txt: %d bytes at %s",file_size, file_path)
    ext = _get_extension(file_path)
    if ext == '.txt':
        logger.debug("loading txt file")
        worked = False
        try:
            encoding, file_handle, words = open_with_correct_encoding(file_path)
        except Exception as e:
            logger.error("Wasn't able to read the words from the file %s" % file_path)
            words = ""
    elif ext == '.docx':
        logger.debug("loading docx file")
        words = _docx_to_txt(file_path)
    elif ext == '.rtf':
        logger.debug("loading rtf file")
        doc = Rtf15Reader.read(open(file_path))
        words = PlaintextWriter.write(doc).getvalue()
    else:
        logging.warning("Couldn't find an extension on the file, so assuming text")
        with codecs.open(file_path, 'r', ENCODING_UTF_8) as myfile:
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
    '''
    Since you can't actually detect the encoding of a file perfectly, default to utf-8
    and fallback to any others we want.  This returns the file handle, and the content, since 
    you have to try to read the file for it to fail on a content encoding error.
    '''
    file_handle = None
    content = ""
    worked = False
    if not worked:
        try:    # try UTF8
            logger.debug("trying to convert_to_txt with %s" % ENCODING_UTF_8)
            myfile = codecs.open(file_path, 'r', ENCODING_UTF_8)
            content = myfile.read()
            encoding = ENCODING_UTF_8
            file_handle = myfile
            worked = True
            logger.debug("file is utf8")
        except Exception as e: 
            logger.warning("convert_to_txt with %s failed on %s" % (ENCODING_UTF_8,file_path))
    if not worked:
        logger.debug("trying to convert_to_txt with %s" % ENCODING_LATIN_1)
        try:    # try latin-1
            myfile = codecs.open(file_path, 'r', ENCODING_LATIN_1)
            content = myfile.read()
            encoding = ENCODING_LATIN_1
            file_handle = myfile
            worked = True
            logger.debug("file is latin1")
        except Exception as e: 
            logger.warning("convert_to_txt with %s failed on %s" % (ENCODING_LATIN_1,file_path))
    if not worked:
        logger.error("Couldn't read txt file in either codec :-(")
    file_handle.seek(0)
    return [encoding, file_handle, content]

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
    try:
        file_name = docs.save(doc)
        file_path = os.path.join(TEMP_DIR, file_name)
        return file_path
    except UploadNotAllowed:
        logger.error("supported filetypes: txt, docx, rtf, csv, xlsx, xls, love")

def open_docs(docs):
    file_paths = []
    for doc in docs:
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
            writer = unicodecsv.writer(f, encoding=ENCODING_UTF_8, delimiter=str(u';'), quotechar=str(u'"'))
            writer.writerows(worksheet.get_all_values())
        file_paths.append(file_path)
    return file_paths

def get_samples(tool_id, lang):
    choices = []
    texts = []
    for text in samples:
        if tool_id in text['modules'] and text['lang'] == lang:
            if(os.path.exists(text['path'])):
                texts.append((text['source'], text['title']))
            else:
                logger.error("%s: file for %s doesn't exist at %s",tool_id, text['source'], text['path'])
    choices = texts
    return choices

def get_sample_title(source):
    for text in samples:
        if source in text['source']:
            return text['title']
    return source

def get_sample_path(source):
    for text in samples:
        if source in text['source']:
            return text['path']
    return source

def get_file_names(file_paths):
    file_names = []
    for f in file_paths:
        file_names.append(_get_file_name(f))
    return file_names

def generate_filename(ext, suffix, *args):
    files = '-'.join(args) + '-' if len(args) > 0 else ''
    suffix = suffix + '-' if suffix is not None and suffix is not '' else ''
    suffix = suffix.replace(' ', '-')
    ext = ext[1:] if '.' in ext[0] else ext
    return files + suffix + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + '.' + ext

def download_webpage(url):
    g = Goose()
    article = g.extract(url=url)
    return {'title': article.title, 'text': article.cleaned_text}

def _open_sheet(workbook, index):
    sh = workbook.sheet_by_index(index)
    name = workbook.sheet_names()[index]
    new_file = _get_temp_file('-' + name + '.csv')
    with open(new_file, 'wb') as f:
        writer = unicodecsv.writer(f, encoding=ENCODING_UTF_8, delimiter=str(u','), quotechar=str(u'"'))
        for row in xrange(sh.nrows):
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
    return textract.process(file_path).decode('utf-8')
