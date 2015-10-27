from .. import mongo
from ..forms import SameDiffUpload, SameDiffSample
from ..logic import filehandler
from flask import Blueprint, render_template, request

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

		if btn_value == 'upload':
			files = request.files.getlist('upload')
			file_paths = filehandler.open_docs(files)
			email = forms['upload'].data['email']
		elif btn_value == 'sample':
			file_paths = forms['sample'].data['samples']
			email = forms['sample'].data['email']

		if btn_value is not None and btn_value is not u'':
			queue_files(file_paths, email)

	return render_template('samediff/samediff.html', forms=sorted(forms.items()))

@mod.route('/results')
def results():
	uuid = None if not 'id' in request.args else request.args['id']
	return render_template('samediff/results.html')

def queue_files(file_paths, email):
	file_names = filehandler.get_file_names(file_paths)
	job_id = mongo.save_queued_files('samediff', file_paths, file_names, email)
	print job_id