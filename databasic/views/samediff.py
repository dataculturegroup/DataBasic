from ..application import mongo, app
from ..forms import SameDiffUpload, SameDiffSample
from ..logic import filehandler
import databasic.tasks
from flask import Blueprint, render_template, request, redirect, url_for, g

mod = Blueprint('samediff', __name__, url_prefix='/<lang_code>/samediff', template_folder='../templates/samediff')

@mod.route('/', methods=('GET', 'POST'))
def index():
	print filehandler.TEMP_DIR
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
	results = mongo.find_document('samediff', doc_id)
	return render_template('samediff/results.html', results=results)

def queue_files(file_paths, is_sample_data, email):
	file_names = filehandler.get_file_names(file_paths)
	job_id = mongo.save_queued_files('samediff', file_paths, file_names, is_sample_data, email, request.url + 'results?id=')
	try:
		result = databasic.tasks.save_tfidf_results.delay(job_id)
	except:
		print "Redis server is not running"
	return redirect(request.url + 'results?id=' + job_id)
