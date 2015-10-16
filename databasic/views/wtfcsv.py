from .. import mongo
from ..forms import WTFCSVForm
from ..logic import wtfcsvstat, filehandler, oauth
from flask import Blueprint, render_template, request, redirect

mod = Blueprint('wtfcsv', __name__, url_prefix='/<lang_code>/wtfcsv', template_folder='../templates/wtfcsv')

@mod.route('/', methods=('GET', 'POST'))
def index():

	form = WTFCSVForm()
	tab = 'paste' if not 'tab' in request.args else request.args['tab']
	results = None

	if request.method == 'POST':
		
		tab = form['input_type'].data

		if form.validate():
			if tab == 'paste':
				results = process_paste(form['area'].data)
			elif tab == 'upload':
				results = process_upload(request.files[form['upload'].name])
			elif tab == 'link':
				doc = oauth.open_doc_from_url(form.data['link'], request.url + "?tab=link")
				if doc['authenticate'] is not None:
					return (redirect(doc['authenticate']))
				else:
					results = process_link(doc['doc'])

			uuid = mongo.save_csv('wtfcsv', results)
			return redirect(request.url + 'results?id=' + uuid)

	return render_template('wtfcsv.html', form=form, tab=tab)

@mod.route('/results')
def results():
	results = None
	uuid = None if not 'id' in request.args else request.args['id']
	if uuid is not None:
		results = mongo.get_document('wtfcsv', uuid).get('results')
		print results
	return render_template('wtfcsv/results.html', results=results)

def process_paste(text):
	file_path = filehandler.write_to_temp_file(text)
	return wtfcsvstat.get_summary(file_path)

def process_upload(csv_file):
	file_path = filehandler.open_doc(csv_file)
	results = wtfcsvstat.get_summary(file_path)
	filehandler.delete_file(file_path)
	return results

def process_link(sheet):
	file_path = filehandler.open_sheet(sheet)
	results = wtfcsvstat.get_summary(file_path)
	filehandler.delete_file(file_path)
	return results
