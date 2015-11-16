from collections import OrderedDict
from ..application import mongo
from ..forms import WTFCSVUpload, WTFCSVLink, WTFCSVSample
from ..logic import wtfcsvstat, filehandler, oauth
from flask import Blueprint, render_template, request, redirect, g
import os, logging

mod = Blueprint('wtfcsv', __name__, url_prefix='/<lang_code>/wtfcsv', template_folder='../templates/wtfcsv')


@mod.route('/', methods=('GET', 'POST'))
def index():
	
	doc_url = oauth.doc_url()
	if doc_url is not None:
		return redirect_to_results(process_link(doc_url))

	tab = 'paste' if not 'tab' in request.args else request.args['tab']
	results = None

	forms = OrderedDict()
	forms['sample'] = WTFCSVSample()
	forms['upload'] = WTFCSVUpload()
	forms['link'] = WTFCSVLink()

	if request.method == 'POST':

		btn_value = request.form['btn']

		if btn_value == 'upload':
			results = process_upload(forms['upload'].data['upload'])
		elif btn_value == 'link':
			doc = oauth.open_doc_from_url(forms['link'].data['link'], request.url)
			if doc['authenticate'] is not None:
				return redirect(doc['authenticate'])
			elif doc['doc'] is not None:
				results = process_link(doc['doc'])
		elif btn_value == 'sample':
			basedir = os.path.dirname(os.path.abspath(__file__))
			sample_file = forms['sample'].data['sample']
			results = []
			results.append(wtfcsvstat.get_summary(os.path.join(basedir,'../','../',sample_file)))

		if btn_value is not None and btn_value is not u'':
			return redirect_to_results(results)

	return render_template('wtfcsv.html', forms=forms.items(), tool_name='wtfcsv')

@mod.route('/results')
def results():
	doc_id = None if not 'id' in request.args else request.args['id']
	if doc_id is None:
		return redirect(g.current_lang + '/wtfcsv')
	else:
		return redirect(g.current_lang + '/wtfcsv/results/0?id=' + doc_id)

@mod.route('/results/<index>')
def results_sheet(index):
	results = None
	doc_id = request.args.get('id', None)
	if doc_id is None:
		return redirect(g.current_lang + '/wtfcsv')
	else:
		results = mongo.find_document('wtfcsv', doc_id).get('results')
	return render_template('wtfcsv/results.html', results=results, tool_name='wtfcsv', index=int(index))

def redirect_to_results(results):
	doc_id = mongo.save_csv('wtfcsv', results)
	return redirect(request.url + 'results?id=' + doc_id)

def process_upload(csv_file):
	file_path = filehandler.open_doc(csv_file)
	file_paths = filehandler.convert_to_csv(file_path)
	results = []
	for f in file_paths:
		summary = wtfcsvstat.get_summary(f)
		summary['sheet_name'] = _get_sheet_name(f)
		results.append(summary)
	filehandler.delete_files(file_paths)
	return results

def process_link(sheet):
	file_paths = filehandler.open_workbook(sheet)
	results = []
	for f in file_paths:
		summary = wtfcsvstat.get_summary(f)
		summary['sheet_name'] = _get_sheet_name(f)
		results.append (summary)
	filehandler.delete_files(file_paths)
	return results

def _get_sheet_name(path):
	return os.path.split(path)[1][16:-4]