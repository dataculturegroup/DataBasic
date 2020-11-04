import logging, os
from collections import OrderedDict
from databasic import mongo, get_base_dir
from databasic.forms import SameDiffUpload, SameDiffSample
from databasic.logic import filehandler
from databasic.logic import textanalysis
from flask import Blueprint, render_template, request, redirect, g, abort, send_from_directory
from flask_babel import lazy_gettext as _

mod = Blueprint('samediff', __name__, url_prefix='/<lang_code>/samediff', template_folder='../templates/samediff')

logger = logging.getLogger(__name__)


@mod.route('/', methods=('GET', 'POST'))
def index():
    
    forms = OrderedDict()
    forms['sample'] = SameDiffSample(g.current_lang)
    forms['upload'] = SameDiffUpload()
    # forms['link'] = SameDiffLink()

    if request.method == 'POST':

        btn_value = request.form['btn']
        titles = []
        sample_id = ''
        file_paths = None

        if btn_value == 'upload':
            files = [forms['upload'].data['upload'], forms['upload'].data['upload2']]
            file_paths = filehandler.open_docs(files)
            f1name = files[0].filename
            f2name = files[1].filename
            logger.debug("New from upload: %s & %s", f1name, f2name)
            both = _('%(f1)s and %(f2)s', f1=f1name, f2=f2name)
            titles = [f1name, str(both), f2name]
            # email = forms['upload'].data['email']
        elif btn_value == 'sample':
            sample_sources = [forms['sample'].data['sample'], forms['sample'].data['sample2']]
            f1name = filehandler.get_sample_title(sample_sources[0])
            f2name = filehandler.get_sample_title(sample_sources[1])
            sample_id = str(f1name) + str(f2name)
            existing_doc_id = mongo.results_for_sample('samediff', sample_id)
            if existing_doc_id is not None:
                logger.debug("Existing from sample: %s", sample_id)
                return redirect(request.url + 'results/' + existing_doc_id)
            logger.debug("New from sample: %s", ", ".join(sample_sources))
            file_paths = [filehandler.get_sample_path(sample_source) for sample_source in sample_sources]
            logger.debug("  loading from %s", ", ".join(file_paths))
            both = str(_('%(f1)s and %(f2)s', f1=f1name, f2=f2name))
            titles = [f1name, both, f2name]
            # email = forms['sample'].data['email']
        elif btn_value == 'link':
            url1 = forms['link'].data['link']
            url2 = forms['link'].data['link2']
            if 'http://' not in url1:
                url1 = 'http://' + url1
            if 'http://' not in url2:
                url2 = 'http://' + url2
            file_paths = [filehandler.write_to_temp_file(filehandler.download_webpage(url1)),
                          filehandler.write_to_temp_file(filehandler.download_webpage(url2))]
            titles = ['1', 'both', '2']

        if btn_value is not None and btn_value != '':
            return process_results(file_paths, titles, sample_id, btn_value)

    return render_template('samediff/samediff.html', forms=list(forms.items()), tool_name='samediff', max_file_size_in_mb = g.max_file_size_mb)


@mod.route('/results/<doc_id>')
def results(doc_id):

    remaining_days = None

    try:
        job = mongo.find_document('samediff', doc_id)
        if job['sample_id'] == '':
            remaining_days = mongo.get_remaining_days('samediff', doc_id)
    except:
        logger.warning("Unable to find doc '%s'", doc_id)
        return render_template('no_results.html', tool_name='samediff')

    whatnext = {
        'most_common_word': job['sameWords'][0][1] if len(job['sameWords']) > 0 else '',
        'second_most_common_word': job['sameWords'][1][1] if len(job['sameWords']) > 1 else '',
        'doc2_most_common_word': job['diffWordsDoc2'][0][1] if len(job['diffWordsDoc2']) > 0 else '',
    }

    if job['totalWordsDoc1'] > job['totalWordsDoc2']:
        pct_length_diff = float(job['totalWordsDoc1'] - job['totalWordsDoc2']) / float(job['totalWordsDoc1'])
    else:
        pct_length_diff = float(job['totalWordsDoc2'] - job['totalWordsDoc1']) / float(job['totalWordsDoc2'])

    return render_template('samediff/results.html', results=job,
                           pct_length_diff=pct_length_diff,
                           cosine_similarity={'score': job['cosineSimilarity'],
                                              'description': interpretCosineSimilarity(job['cosineSimilarity'])},
                           whatnext=whatnext, tool_name='samediff', doc_id=doc_id,
                           remaining_days=remaining_days)


@mod.route('/results/download/<doc_id>/results.csv')
def download(doc_id):
    try:
        logger.debug("Download %s", doc_id)
        doc = mongo.find_document('samediff', doc_id)
        headers = [_('word'), _('uses in') + ' ' + doc['filenames'][0], _('uses in') + ' ' + doc['filenames'][1], _('total uses')]
        rows = []
        for f, w in doc['sameWords']:
            doc_1_count = next(f2 for f2, w2 in doc['mostFrequentDoc1'] if w == w2)
            doc_2_count = next(f2 for f2, w2 in doc['mostFrequentDoc2'] if w == w2)
            rows.append([w, doc_1_count, doc_2_count, f])
        for f, w in doc['diffWordsDoc1']:
            rows.append([w, f, 0, f])
        for f, w in doc['diffWordsDoc1']:
            rows.append([w, 0, f, f])
        # TODO: clean up file name
        file_path = filehandler.write_to_csv(headers, rows,
                                             filehandler.generate_filename('csv', '', doc['filenames'][0], doc['filenames'][1]),
                                             False)
        logger.debug('  created csv to download at %s', file_path)
        return filehandler.generate_csv(file_path)
    except Exception as e:
        logging.exception(e)
        abort(400)


@mod.route('/samediff-activity-guide.pdf')
def download_activity_guide():
    filename = "SameDiff Activity Guide.pdf"
    dir_path = os.path.join(get_base_dir(), 'databasic', 'static', 'files', 'activity-guides', g.current_lang)
    logger.debug("download activity guide from %s/%s", dir_path, filename)
    return send_from_directory(directory=dir_path, filename=filename)


def process_results(file_paths, titles, sample_id, source):
    file_names = filehandler.get_file_names(file_paths)
    file_sizes = [str(os.stat(file_path).st_size) for file_path in file_paths]  # because browser might not have sent content_length
    logger.debug("Upload: %s bytes", ", ".join(file_sizes))
    doc_list = [filehandler.convert_to_txt(file_path) for file_path in file_paths]
    data = textanalysis.common_and_unique_word_freqs(doc_list)
    job_id = mongo.save_samediff('samediff', file_names,
                                 data['doc1total'], data['doc2total'],
                                 data['doc1unique'], data['doc2unique'],
                                 data['common'], data['common_counts'],
                                 data['doc1'], data['doc2'], data['cosine_similarity'],
                                 titles,
                                 sample_id,
                                 source)
    return redirect(request.url + 'results/' + job_id + '?submit=true')


def interpretCosineSimilarity(score):
    # Cosine Similarity
    if score >= 0.9:
        return _('almost the same')
    elif score >= 0.8:
        return _('sort of similar')
    elif score >= 0.7:
        return _('kind of similar')
    elif score >= 0.5:
        return _('kind of similar, and also kind of different')
    elif score >= 0.3:
        return _('pretty different')
    elif score >= 0.2:
        return _('very different')
    else:
        return _('completely different')


def stream_csv(data, prop_names, col_names):
    yield ','.join(col_names) + '\n'
    for row in data:
        try:
            attributes = []
            for p in prop_names:
                value = row[p]
                if isinstance(value, (int, float)):
                    cleaned_value = str(row[p])
                else:
                    cleaned_value = '"'+value.encode('utf-8').replace('"', '""')+'"'
                attributes.append(cleaned_value)
            yield ','.join(attributes) + '\n'
        except Exception as e:
            logger.error("Couldn't process a CSV row: "+str(e))
            logger.debug(e)
            logger.debug(row)
