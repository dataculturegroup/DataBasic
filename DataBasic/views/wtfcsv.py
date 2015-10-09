from ..forms import WTFCSVForm
from ..logic import wtfcsvstat, FileHandler
from flask import Blueprint, render_template, request

mod = Blueprint('wtfcsv', __name__, url_prefix='/<lang_code>/wtfcsv', template_folder='../templates/wtfcsv')

@mod.route('/', methods=('GET', 'POST'))
def index():

	results = None
	form = WTFCSVForm()
	tab = 'paste'

	if request.method == 'POST' and form.validate():
		tab = form['input_type'].data
		if tab == 'paste':
			results = process_paste(form['area'].data)
		elif tab == 'upload':
			results = process_upload(request.files[form['upload'].name])

	return render_template('wtfcsv.html', form=form, tab=tab, results=results)

def process_paste(text):
	file_path = FileHandler.write_to_temp_file(text)
	return wtfcsvstat.get_summary(file_path)

def process_upload(csv_file):
	file_path = FileHandler.open_csv(csv_file)
	results = wtfcsvstat.get_summary(file_path)
	FileHandler.delete_file(file_path)
	return results

def process_link():
	pass