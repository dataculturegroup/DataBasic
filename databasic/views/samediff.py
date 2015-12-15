import datetime, logging, json, os
from operator import itemgetter
from collections import OrderedDict
from databasic import mongo, app, get_base_dir
#form databasic import mail
from databasic.forms import SameDiffUpload, SameDiffSample, SameDiffLink
from databasic.logic import filehandler
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
	# forms['link'] = SameDiffLink()

	if request.method == 'POST':

		btn_value = request.form['btn']
		# email = None
		is_sample_data = False
		titles = []
		sample_id = []

		if btn_value == 'upload':
			files = [forms['upload'].data['upload'], forms['upload'].data['upload2']]
			file_paths = filehandler.open_docs(files)
			f1name = files[0].filename
			f2name = files[1].filename
			both = unicode(_('%(f1)s and %(f2)s', f1=f1name, f2=f2name))
			titles = [f1name, both, f2name]
			# email = forms['upload'].data['email']
		elif btn_value == 'sample':
			file_paths = [ os.path.join(get_base_dir(),forms['sample'].data['sample']),
						   os.path.join(get_base_dir(),forms['sample'].data['sample2']) ]
			is_sample_data = True
			f1name = filehandler.get_sample_title(forms['sample'].data['sample'])
			f2name = filehandler.get_sample_title(forms['sample'].data['sample2'])
			both = unicode(_('%(f1)s and %(f2)s', f1=f1name, f2=f2name))
			titles = [f1name, both, f2name]
			sample_id = str(f1name) + str(f2name)
			# email = forms['sample'].data['email']
		elif btn_value == 'link':
			url1 = forms['link'].data['link']
			url2 = forms['link'].data['link2']
			if not 'http://' in url1:
				url1 = 'http://' + url1
			if not 'http://' in url2:
				url2 = 'http://' + url2
			file_paths = [ filehandler.write_to_temp_file(filehandler.download_webpage(url1)), 
						   filehandler.write_to_temp_file(filehandler.download_webpage(url2)) ]
			titles = ['1', 'both', '2']

		if btn_value is not None and btn_value is not u'':
			return process_results(file_paths, titles, sample_id)

	return render_template('samediff/samediff.html', forms=forms.items(), tool_name='samediff')

@mod.route('/results/<doc_id>')
def results(doc_id):

	job = mongo.find_document('samediff', doc_id)

	whatnext = {}
	whatnext['most_common_word'] = job['sameWords'][0][1] if len(job['sameWords']) > 0 else ''
	whatnext['second_most_common_word'] = job['sameWords'][1][1] if len(job['sameWords']) > 1 else ''
	whatnext['doc2_most_common_word'] = job['diffWordsDoc2'][0][1] if len(job['diffWordsDoc2']) > 0 else ''

	return render_template('samediff/results.html', results=job, 
		cosine_similarity= {'score':job['cosineSimilarity'],'description':interpretCosineSimilarity(job['cosineSimilarity'])},
		whatnext=whatnext, tool_name='samediff', doc_id=doc_id)

@mod.route('/results/download/<doc_id>/results.csv')
def download(doc_id):
	try:
		doc = mongo.find_document('samediff', doc_id)
		headers = [_('word'), _('uses in') +' ' + doc['filenames'][0], _('uses in') + ' ' + doc['filenames'][1], _('total uses')]
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
			filehandler.generate_filename('csv', '', doc['filenames'][0], doc['filenames'][1]), False)
		return filehandler.generate_csv(filename)
	except Exception as e:
		logging.exception(e)
		abort(400)

def process_results(file_paths, titles, sample_id):
	file_names = filehandler.get_file_names(file_paths)
	doc_list = [ filehandler.convert_to_txt(file_path) for file_path in file_paths ]
	data = textanalysis.common_and_unique_word_freqs(doc_list)
	job_id = mongo.save_samediff('samediff', file_names, 
		data['doc1unique'], data['doc2unique'], data['common'], data['common_counts'],
		data['doc1'], data['doc2'], data['cosine_similarity'],
		titles,
		sample_id)
	return redirect(request.url + 'results/' + job_id)

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