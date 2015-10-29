from ..application import mongo, app, mail
from ..forms import SameDiffUpload, SameDiffSample
from ..logic import filehandler
import databasic.tasks
from flask import Blueprint, render_template, request, redirect, url_for, g
from flask.ext.babel import lazy_gettext as _

mod = Blueprint('samediff', __name__, url_prefix='/<lang_code>/samediff', template_folder='../templates/samediff')

@mod.route('/', methods=('GET', 'POST'))
def index():
	
	forms = {
		'upload': SameDiffUpload(),
		'sample': SameDiffSample()
	}

	if request.method == 'POST':

		btn_value = request.form['btn']
		email = None
		is_sample_data = False

		if btn_value == 'upload':
			files = request.files.getlist('upload')
			file_paths = filehandler.open_docs(files)
			email = forms['upload'].data['email']
		elif btn_value == 'sample':
			file_paths = forms['sample'].data['samples']
			is_sample_data = True
			email = forms['sample'].data['email']

		if btn_value is not None and btn_value is not u'':
			return queue_files(file_paths, is_sample_data, email)

	return render_template('samediff/samediff.html', forms=sorted(forms.items()))

@mod.route('/results')
def results():

	doc_id = None if not 'id' in request.args else request.args['id']
	if doc_id is None:
		return redirect(g.current_lang + '/samediff')

	job = mongo.find_document('samediff', doc_id)

	# kind of a hacky way of checking if the job is ready but for some reason 'status' is returning 'complete' prematurely
	if not job.has_key('cosineSimilarity'):
		return render_template('samediff/results.html', results=job)

	# interpret cosine similarity for top part of report 
	# If there are only 2 docs then make a statement about how similar they are to each other
	if len(job['filenames']) == 2:
		cosineDiff = abs(job['cosineSimilarity'][0][0] - job['cosineSimilarity'][0][1])
		job['humanReadableSimilarity'] = interpretCosineSimilarity(cosineDiff)
	else:
		maxInfo = {'score':0}
		minInfo = {'score':1}
		for r in range(len(job['filenames'])):
			for c in range(r+1,len(job['filenames'])):
				score = job['cosineSimilarity'][r][c]
				if score >= maxInfo['score']:
					maxInfo = { 'score':score, 'doc1':r, 'doc2':c}
				if score <= minInfo['score']:
					minInfo = { 'score':score, 'doc1':r, 'doc2':c}

		job['mostSimilar'] = [ job['filenames'][maxInfo['doc1']], job['filenames'][maxInfo['doc2']] ]
		job['mostDifferent'] = [ job['filenames'][minInfo['doc1']], job['filenames'][minInfo['doc2']] ]
	#	
	# Find the lowest average cosine similarity to figure out which doc is the most unique
	#
	averages = []
	for fileCS in job['cosineSimilarity']:
		averageSimilarity = 0
		for cs in fileCS:
			averageSimilarity = averageSimilarity + cs
		averages.append( averageSimilarity / len(job['filenames']) )

	minCS = min(averages)
	mins = [i for i, j in enumerate(averages) if j == minCS]
	
	job['mostDifferentFile'] = job['filenames'][mins[0]]

	return render_template('samediff/results.html', results=job)

def queue_files(file_paths, is_sample_data, email):
	file_names = filehandler.get_file_names(file_paths)
	job_id = mongo.save_queued_files('samediff', file_paths, file_names, is_sample_data, email, request.url + 'results?id=')
	result = databasic.tasks.save_tfidf_results.delay(job_id)
	print result
	return redirect(request.url + 'results?id=' + job_id)

def interpretCosineSimilarity(cosineDiff):
	# Cosine Similarity
	if cosineDiff <= 0.1:
		return _('similar')
	elif cosineDiff <= 0.2:
		return _('sort of similar')
	elif cosineDiff <= 0.3:
		return _('pretty different')
	else:
		return _('very different')