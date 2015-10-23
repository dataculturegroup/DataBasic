from ..forms import SameDiffUpload
from flask import Blueprint, render_template

mod = Blueprint('samediff', __name__, url_prefix='/<lang_code>/samediff', template_folder='../templates/samediff')

@mod.route('/')
def index():
	
	forms = {
		'upload': SameDiffUpload()
	}

	return render_template('samediff/samediff.html', forms=sorted(forms.items()))

@mod.route('/results')
def results():
	return render_template('samediff/results.html')