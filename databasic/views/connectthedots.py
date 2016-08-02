import logging, os
from collections import OrderedDict
from databasic import mongo
from databasic.forms import ConnectTheDotsUpload, ConnectTheDotsSample
from databasic.logic import connectthedots, filehandler
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

    if request.method == 'POST':
        btn_value = request.form['btn']
        sample_id = ''

        if btn_value == 'sample':
            sample_source = forms['sample'].data['sample']
            sample_name = filehandler.get_sample_title(sample_source)
            sample_id = sample_source
            existing_doc_id = mongo.results_for_sample('connectthedots', sample_id)
            if existing_doc_id is not None:
                logger.debug("[CTD] Sample already in database: %s", sample_source)
                return redirect(request.url + 'results/' + existing_doc_id)
            logger.debug("[CTD] New doc from sample: %s", sample_name)
            sample_path = filehandler.get_sample_path(sample_source)
            logger.debug("      Loading from: %s", sample_path)
            results = []
            results.append(connectthedots.get_summary(sample_path))
            results[0]['filename'] = sample_name + '.csv'
            
            if os.environ['APP_MODE'] == 'development':
                del results[0]['graph']

        if btn_value is not None and btn_value is not u'':
            return redirect_to_results(results, btn_value, sample_id)

    return render_template('connectthedots.html',
                           forms=forms.items(),
                           tool_name='connectthedots',
                           max_file_size_in_mb = g.max_file_size_mb)

@mod.route('/results/<doc_id>')
def results(doc_id):
    try:
        results = mongo.find_document('connectthedots', doc_id).get('results')
        logger.info("[CTD] Showing results for %s", doc_id)
        return render_results(doc_id, 0)
    except:
        logger.warning("[CTD] Unable to find doc: %s", doc_id)
        return render_template('no_results.html', tool_name='connectthedots')

def redirect_to_results(results, source, sample_id=''):
    doc_id = mongo.save_csv('connectthedots', results, sample_id, source)
    return redirect(g.current_lang + '/connectthedots/results/' + doc_id + '?submit=true')

def render_results(doc_id, sheet_idx):
    doc = mongo.find_document('connectthedots', doc_id)
    results = doc.get('results')

    return render_template('connectthedots/results.html', 
        results=results,
        tool_name='connectthedots', 
        index=int(sheet_idx),
        source=doc['source'])