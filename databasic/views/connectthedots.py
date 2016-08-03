import logging, os
from collections import OrderedDict
from databasic import mongo
from databasic.forms import ConnectTheDotsUpload, ConnectTheDotsSample
from databasic.logic import connectthedots as ctd, filehandler
from flask import Blueprint, g, redirect, render_template, request

mod = Blueprint('connectthedots', __name__,
                url_prefix='/<lang_code>/connectthedots',
                template_folder='../templates/connectthedots')

logger = logging.getLogger(__name__)

@mod.route('/', methods=('GET', 'POST'))
def index():
    forms = OrderedDict()
    forms['sample'] = ConnectTheDotsSample(g.current_lang)
    forms['upload'] = ConnectTheDotsUpload()
    upload_failed = False

    if request.method == 'POST':
        btn_value = request.form['btn']
        sample_id = ''

        # Sample file
        if btn_value == 'sample':
            sample_source = forms['sample'].data['sample']
            existing_doc_id = mongo.results_for_sample('connectthedots', sample_source)
            if existing_doc_id is not None:
                logger.debug('[CTD] Sample already in database: %s', sample_source)
                return redirect(request.url + 'results/' + existing_doc_id)
            else:
                sample_name = filehandler.get_sample_title(sample_source)
                sample_id = sample_source
                logger.debug('[CTD] New doc from sample: %s', sample_name)
                results = process_sample(sample_source)

        # File upload
        elif btn_value == 'upload':
            upload_file = forms['upload'].data['upload']
            has_header_row = forms['upload'].data['has_header_row']
            logger.debug('[CTD] New doc from upload: %s', upload_file.filename)
            results = process_upload(upload_file, has_header_row)

        if btn_value is not None and btn_value is not u'' and results:
            return redirect_to_results(results, btn_value, sample_id)
        else:
            upload_failed = True

    return render_template('connectthedots.html',
                           forms=forms.items(),
                           tool_name='connectthedots',
                           max_file_size_in_mb=g.max_file_size_mb,
                           upload_failed=upload_failed)

def process_sample(source):        
    sample_name = filehandler.get_sample_title(source)
    sample_path = filehandler.get_sample_path(source)
    logger.debug('[CTD] Loading from: %s', sample_path)

    results = []
    results.append(ctd.get_summary(sample_path))
    results[0]['filename'] = sample_name + '.csv'
    
    if os.environ['APP_MODE'] == 'development':
        del results[0]['graph']

    return results

def process_upload(file, has_header_row=True):
    file_path = filehandler.open_doc(file)
    file_name = file.filename
    file_size = os.stat(file_path).st_size
    logger.debug('[CTD] File size: %d bytes', file_size)

    results = []
    file_paths = filehandler.convert_to_csv(file_path)

    for f in file_paths:
        summary = ctd.get_summary(f, has_header_row)
        if not summary:
            continue
        summary['sheet_name'] = get_sheet_name(f)
        summary['filename'] = file_name
        if os.environ['APP_MODE'] == 'development':
            del summary['graph']
        results.append(summary)

    filehandler.delete_files(file_paths)
    return results

def get_sheet_name(path):
    return os.path.split(path)[1][16:-4]

def redirect_to_results(results, source, sample_id=''):
    doc_id = mongo.save_csv('connectthedots', results, sample_id, source)
    return redirect(g.current_lang + '/connectthedots/results/' + doc_id + '?submit=true')

@mod.route('/results/<doc_id>')
def results(doc_id):
    try:
        results = mongo.find_document('connectthedots', doc_id).get('results')
        logger.info('[CTD] Showing results for %s', doc_id)
        return render_results(doc_id)
    except:
        logger.warning('[CTD] Unable to find doc: %s', doc_id)
        return render_template('no_results.html', tool_name='connectthedots')

def render_results(doc_id):
    doc = mongo.find_document('connectthedots', doc_id)
    results = doc.get('results')

    return render_template('connectthedots/results.html', 
        results=results,
        tool_name='connectthedots',
        source=doc['source'])