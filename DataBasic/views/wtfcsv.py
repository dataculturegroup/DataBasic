from ..forms import WTFCSVForm
from ..logic import wtfcsvstat, FileHandler, OAuthHandler
from flask import Blueprint, render_template, request, redirect

mod = Blueprint('wtfcsv', __name__, url_prefix='/<lang_code>/wtfcsv', template_folder='../templates/wtfcsv')

@mod.route('/', methods=('GET', 'POST'))
def index():

	results = None
	form = WTFCSVForm()
	tab = 'paste'

	if request.method == 'POST':
		
		tab = form['input_type'].data

		if form.validate():
			if tab == 'paste':
				results = process_paste(form['area'].data)
			elif tab == 'upload':
				results = process_upload(request.files[form['upload'].name])
			elif tab == 'link':
				doc = OAuthHandler.open_doc_from_url(form.data['link'], request.url)
				if doc['authenticate'] is not None:
					return (redirect(doc['authenticate']))
				else:
					print doc['doc']

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