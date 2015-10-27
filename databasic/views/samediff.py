from ..forms import SameDiffUpload, SameDiffSample
from flask import Blueprint, render_template, request

mod = Blueprint('samediff', __name__, url_prefix='/<lang_code>/samediff', template_folder='../templates/samediff')

@mod.route('/', methods=('GET', 'POST'))
def index():
	
	forms = {
		'upload': SameDiffUpload(),
		'sample': SameDiffSample()
	}

	if request.method == 'POST':
		pass

	return render_template('samediff/samediff.html', forms=sorted(forms.items()))

@mod.route('/results')
def results():
	return render_template('samediff/results.html')