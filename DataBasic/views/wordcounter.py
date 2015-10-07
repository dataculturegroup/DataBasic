from .. import app
from ..forms import WordCountForm
from ..logic import WordCounter
from flask import Blueprint, render_template, request, redirect

mod = Blueprint('wordcounter', __name__, url_prefix='/<lang_code>/wordcounter', template_folder='../templates/wordcounter')

"""
@app.route('/', subdomain='wordcounter')
def index():
	return render_template('wordcounter/index.html')
"""

@mod.route('/', methods=('GET', 'POST'))
def index():

	counts = []
	form = WordCountForm()

	if request.method == 'POST' and form.validate():
		counts = WordCounter.get_word_counts(
			form.data['area'],
			form.data['ignore_case'],
			form.data['ignore_stopwords'])

	return render_template('index.html', form=form, results=counts)
