from .. import mongo
from ..forms import WTFCSVPaste, WTFCSVUpload, WTFCSVLink
from ..logic import wtfcsvstat, filehandler, oauth
from flask import Blueprint, render_template, request, redirect

mod = Blueprint('wtfcsv', __name__, url_prefix='/<lang_code>/wtfcsv', template_folder='../templates/wtfcsv')

@mod.route('/', methods=('GET', 'POST'))
def index():

	tab = 'paste' if not 'tab' in request.args else request.args['tab']
	results = None

	forms = {
		'paste': WTFCSVPaste('name, shirt_color, siblings\nRahul, blue, 1\nCatherine, red, 2'),
		'upload': WTFCSVUpload(),
		'link': WTFCSVLink()
	}

	if request.method == 'POST':

		btn_value = request.form['btn']

		if btn_value == 'paste':
			results = process_paste(forms['paste'].area.data)
		elif btn_value == 'upload':
			results = process_upload(request.files[forms['upload'].data.name])
		elif btn_value == 'link':
			doc = oauth.open_doc_from_url(forms['link'].data['link'], request.url + "?tab=link")
			if doc['authenticate'] is not None:
				return (redirect(doc['authenticate']))
			else:
				results = process_link(doc['doc'])

		if btn_value is not None and btn_value is not u'':
			uuid = mongo.save_csv('wtfcsv', results)
			return redirect(request.url + 'results?id=' + uuid)

	return render_template('wtfcsv.html', forms=sorted(forms.items()))#, tab=tab)

@mod.route('/results')
def results():
	results = None
	uuid = None if not 'id' in request.args else request.args['id']
	if uuid is not None:
		results = mongo.get_document('wtfcsv', uuid).get('results')
		print results['row_count']
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
