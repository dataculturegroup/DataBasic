import datetime, logging, json
from operator import itemgetter
from collections import OrderedDict
from ..application import mongo, app, mail
from ..forms import SameDiffUpload, SameDiffSample
from ..logic import filehandler
import databasic.tasks
from databasic.logic import tfidfanalysis, textanalysis
from flask import Blueprint, render_template, request, redirect, url_for, g, abort, Response
from flask.ext.babel import lazy_gettext as _

mod = Blueprint('samediff', __name__, url_prefix='/<lang_code>/samediff', template_folder='../templates/samediff')

@mod.route('/', methods=('GET', 'POST'))
def index():

	forms = OrderedDict()
	forms['sample'] = SameDiffSample()
	forms['upload'] = SameDiffUpload()

	if request.method == 'POST':

		btn_value = request.form['btn']
		# email = None
		is_sample_data = False

		if btn_value == 'upload':
			files = [forms['upload'].data['upload'], forms['upload'].data['upload2']]
			file_paths = filehandler.open_docs(files)
			# email = forms['upload'].data['email']
		elif btn_value == 'sample':
			file_paths = [forms['sample'].data['sample'], forms['sample'].data['sample2']]
			is_sample_data = True
			# email = forms['sample'].data['email']

		if btn_value is not None and btn_value is not u'':
			return process_results(file_paths)

	return render_template('samediff/samediff.html', forms=forms.items(), tool_name='samediff')

@mod.route('/results')
def results():

	doc_id = None if not 'id' in request.args else request.args['id']
	if doc_id is None:
		return redirect(g.current_lang + '/samediff')

	job = mongo.find_document('samediff', doc_id)

	whatnext = {}
	whatnext['most_common_word'] = job['sameWords'][0][1] if len(job['sameWords']) > 0 else ''
	whatnext['second_most_common_word'] = job['sameWords'][1][1] if len(job['sameWords']) > 1 else ''
	whatnext['doc2_most_common_word'] = job['diffWordsDoc2'][0][1] if len(job['diffWordsDoc2']) > 0 else ''

	return render_template('samediff/results.html', results=job, 
		cosine_similarity= {'score':job['cosineSimilarity'],'description':interpretCosineSimilarity(job['cosineSimilarity'])},
		whatnext=whatnext, tool_name='samediff')

@mod.route('/results/download/<doc_id>/<filename1>-<filename2>-samediff.csv')
def download(doc_id, filename1, filename2):
	try:
		doc = mongo.find_document('samediff', doc_id)
		headers = [_('word'), _('uses in') +' ' + str(filename1), _('uses in') + ' ' + str(filename2), _('total uses')]
		rows = []
		for f, w in doc['sameWords']:
			doc1Count = next(f2 for f2, w2 in doc['mostFrequentDoc1'] if w == w2)
			doc2Count = next(f2 for f2, w2 in doc['mostFrequentDoc2'] if w == w2)
			rows.append([w, doc1Count, doc2Count, f])
		for f, w in doc['diffWordsDoc1']:
			rows.append([w, f, 0, f])
		for f, w in doc['diffWordsDoc1']:
			rows.append([w, 0, f, f])
		# TODO: clean up file name
		filename = filehandler.write_to_csv(headers, rows, 
			filehandler.generate_filename('csv', 'samediff', filename1, filename2))
		return filehandler.generate_csv(filename)
	except Exception as e:
		logging.exception(e)
		abort(400)

def process_results(file_paths):
	file_names = filehandler.get_file_names(file_paths)
	doc_list = [ filehandler.convert_to_txt(file_path) for file_path in file_paths ]
	data = textanalysis.common_and_unique_word_freqs(doc_list)
	job_id = mongo.save_samediff('samediff', file_names, 
		data['doc1unique'], data['doc2unique'], data['common'], 
		data['doc1'], data['doc2'], data['cosine_similarity'])
	return redirect(request.url + 'results?id=' + job_id)

def interpretCosineSimilarity(score):
	# Cosine Similarity
	if score >= 0.9:
		return _('almost_the_same')
	elif score >= 0.8:
		return _('sort of similar')
	elif score >= 0.7:
		return _('kind of similar')
	elif score >= 0.5:
		return _('kind of similar, kind of different')
	elif score >= 0.3:
		return _('pretty different')
	elif score >= 0.2:
		return _('very different')
	else:
		return _('completely different')

def stream_csv(data,prop_names,col_names):
    yield ','.join(col_names) + '\n'
    for row in data:
        try:
            attributes = []
            for p in prop_names:
                value = row[p]
                cleaned_value = value
                if isinstance( value, ( int, long, float ) ):
                    cleaned_value = str(row[p])
                else:
                    cleaned_value = '"'+value.encode('utf-8').replace('"','""')+'"'
                attributes.append(cleaned_value)
            yield ','.join(attributes) + '\n'
        except Exception as e:
            print "Couldn't process a CSV row: "+str(e)
            print e
            print row