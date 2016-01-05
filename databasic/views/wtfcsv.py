import json, logging
from collections import OrderedDict
from databasic import mongo, get_base_dir
from databasic.forms import WTFCSVUpload, WTFCSVLink, WTFCSVSample
from databasic.logic import wtfcsvstat, filehandler, oauth
from flask import Blueprint, render_template, request, redirect, g, abort, send_from_directory
from flask.ext.babel import gettext, ngettext
import os, logging, random

mod = Blueprint('wtfcsv', __name__, url_prefix='/<lang_code>/wtfcsv', template_folder='../templates/wtfcsv')

logger = logging.getLogger(__name__)

@mod.route('/', methods=('GET', 'POST'))
def index():
    
    mongo.clear_collection('wtfcsv')
    doc_url = oauth.doc_url()
    if doc_url is not None:
        return redirect_to_results(process_link(doc_url), 'link')

    tab = 'paste' if not 'tab' in request.args else request.args['tab']
    results = None

    forms = OrderedDict()
    forms['sample'] = WTFCSVSample()
    forms['upload'] = WTFCSVUpload()
    # forms['link'] = WTFCSVLink()

    if request.method == 'POST':

        btn_value = request.form['btn']
        sample_id = ''

        if btn_value == 'upload':
            upload_file = forms['upload'].data['upload']
            logger.debug("New from upload: %s", upload_file.filename)
            results = process_upload(upload_file)
        elif btn_value == 'link':
            doc_url = forms['link'].data['link']
            logger.debug("New from link: %s", doc_url)
            doc = oauth.open_doc_from_url(doc_url, request.url)
            if doc['authenticate'] is not None:
                return redirect(doc['authenticate'])
            elif doc['doc'] is not None:
                results = process_link(doc['doc'])
        elif btn_value == 'sample':
            basedir = os.path.dirname(os.path.abspath(__file__))
            sample_source = forms['sample'].data['sample']
            logger.debug("New from sample: %s", sample_source)
            sample_path = filehandler.get_sample_path(sample_source)
            logger.debug("  loading from %s", sample_path)
            results = []
            results.append(wtfcsvstat.get_summary(sample_path))
            results[0]['filename'] = filehandler.get_sample_title(sample_source) + '.csv'

        if btn_value is not None and btn_value is not u'':
            return redirect_to_results(results, btn_value, sample_id)

    return render_template('wtfcsv.html', forms=forms.items(), tool_name='wtfcsv')

@mod.route('/results/<doc_id>')
def results(doc_id):
    try:
        results = mongo.find_document('wtfcsv', doc_id).get('results')
        if len(results) > 1:
            submit = request.args.get('submit', '')
            param = '?submit=true' if 'true' in submit else ''
            return redirect(g.current_lang + '/wtfcsv/results/' + doc_id + '/sheets/0' + param)
        else:
            return render_results(doc_id, 0)
    except:
        logger.warning("Unable to find doc '%s'", doc_id)
        abort(400)

@mod.route('/results/<doc_id>/sheets/<sheet_idx>')
def results_sheet(doc_id, sheet_idx):
    return render_results(doc_id, sheet_idx)

@mod.route('/wtfcsv-activity-guide.pdf')
def download_activity_guide():
    filename = None
    if g.current_lang == 'en':
        filename = "WTFcsv Activity Guide v1_0_0.pdf"
    if filename is None:
        abort(500)
    files_path = os.path.join(get_base_dir(),'databasic','static','files')
    return send_from_directory(directory=files_path, filename=filename)

def render_results(doc_id, sheet_idx):

    doc = mongo.find_document('wtfcsv', doc_id)
    results = doc.get('results')

    if 'bad_formatting' in results:
        return render_template('wtfcsv/results.html', results=results, tool_name='wtfcsv', index=0)

    def get_random_column():
        return random.choice(results[int(sheet_idx)]['columns'])

    columns = results[int(sheet_idx)]['columns']

    if len(columns) < 1:
        whatnext = 'no_data'
    else:
        random_column = get_random_column()
        random_column2 = get_random_column()
        random_column3 = get_random_column()

        if len(columns) > 0 and next((c for c in columns if 'most_freq_values' in c), None) is not None:
            while 'most_freq_values' not in random_column:
                random_column = get_random_column()

        if len(columns) > 1:
            while random_column2 == random_column:
                random_column2 = get_random_column()
        else:
            random_column2 = random_column
        
        if len(columns) > 2:
            while random_column3 == random_column or random_column3 == random_column2:
                random_column3 = get_random_column()
        else:
            random_column3 = random_column

        whatnext = {}
        if 'most_freq_values' in random_column and len(random_column['most_freq_values']) > 0:
            whatnext['random_column_top_value'] = random_column['most_freq_values'][0]['value'] if 'most_freq_values' in random_column else ''
        else:
            whatnext['random_column_top_value'] = 0
        whatnext['random_column_name'] = random_column['name']
        whatnext['random_column_name2'] = random_column2['name']
        whatnext['random_column_name3'] = random_column3['name']

    # build a list of summary result data for the chart
    for col in columns:
        is_string = 'text' in col['display_type_name']
        data_to_use = []
        # pick the right results to summarize
        if 'deciles' in col:
            data_to_use = col['deciles']
        elif 'most_freq_values' in col:
            data_to_use = col['most_freq_values']
        elif 'word_counts' in col:
            data_to_use = [ {'value':r[0], 'count':r[1]} for r in col['word_counts'][0][:20] ]
        # stitch together the overview
        overview_data = {'categories':[],'values':[]}
        for d in data_to_use:
            key = str(d['value']) if is_string else str(d['value']).replace('_', '.')
            overview_data['categories'].append(key)
            overview_data['values'].append(d['count'])
        if 'others' in col:
            overview_data['categories'].append(gettext('Other'))
            overview_data['values'].append(int(col['others']))
        col['overview'] = overview_data
    
    return render_template('wtfcsv/results.html', results=results, whatnext=whatnext, tool_name='wtfcsv', index=int(sheet_idx), source=doc['source'])

def redirect_to_results(results, source, sample_id=''):
    doc_id = mongo.save_csv('wtfcsv', results, sample_id, source)
    return redirect(g.current_lang + '/wtfcsv/results/' + doc_id + '?submit=true')

def process_upload(csv_file):
    file_path = filehandler.open_doc(csv_file)
    file_size = os.stat(file_path).st_size # because browser might not have sent content_length
    logger.debug("Upload: %d bytes", file_size)
    file_paths = filehandler.convert_to_csv(file_path)
    results = []
    for f in file_paths:
        summary = wtfcsvstat.get_summary(f)
        if 'bad_formatting' not in summary:
            summary['sheet_name'] = _get_sheet_name(f)
            summary['filename'] = csv_file.filename
        results.append(summary)
    filehandler.delete_files(file_paths)
    return results

def process_link(sheet):
    file_paths = filehandler.open_workbook(sheet)
    results = []
    for f in file_paths:
        summary = wtfcsvstat.get_summary(f)
        if 'bad_formatting' not in summary:
            summary['sheet_name'] = _get_sheet_name(f)
            summary['filename'] = sheet.sheet1.title
        results.append (summary)
    filehandler.delete_files(file_paths)
    return results

def _get_sheet_name(path):
    return os.path.split(path)[1][16:-4]
    