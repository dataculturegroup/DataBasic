from .. import app
from ..forms import WordCountForm
from ..logic import WordHandler, FileHandler
from flask import Blueprint, render_template, request

mod = Blueprint('wordcounter', __name__, url_prefix='/<lang_code>/wordcounter', template_folder='../templates/wordcounter')

"""
@app.route('/', subdomain='wordcounter')
def index():
	return render_template('wordcounter/index.html')
"""

@mod.route('/', methods=('GET', 'POST'))
def index():

	counts = []
	csv_files = []
	form = WordCountForm()
	tab = 'paste'

	if request.method == 'POST' and form.validate():
		
		tab = form['input_type'].data
		words = None

		# use the uploaded text if it exists, otherwise use the text in the text area
		# TODO: should toggle what's visible to the player instead (same as how WTFcsv handles multiple inputs)
		upload = form.data['upload']
		if upload is not None:
			words = FileHandler.convert_to_txt(upload)
		else:
			words = form.data['area']

		# calculate counts
		counts = WordHandler.get_word_counts(
			words,
			form.data['ignore_case'],
			form.data['ignore_stopwords'])

		# create the csvs
		csv_files = create_csv_files(counts)

	return render_template('wordcounter.html', form=form, tab=tab, results=counts, csv_files=csv_files)

@mod.route('/download-csv/<file_path>')
def download_csv(file_path):
	return FileHandler.generate_csv(file_path)

def create_csv_files(counts):
	files = []
	files.append(FileHandler.write_to_csv(['word', 'frequency'], counts[0], '-word-counts.csv'))

	bigrams = []
	for w in counts[1]:
		freq = w[1]
		phrase = " ".join(w[0])
		bigrams.append([phrase, freq])

	files.append(FileHandler.write_to_csv(['bigram phrase', 'frequency'], bigrams, '-bigram-counts.csv'))
	
	trigrams = []
	for w in counts[2]:
		freq = w[1]
		phrase = " ".join(w[0])
		trigrams.append([phrase, freq])

	files.append(FileHandler.write_to_csv(['trigram phrase', 'frequency'], trigrams, '-trigram-counts.csv'))
	return files
