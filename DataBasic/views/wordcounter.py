# from DataBasic import app 
from flask import Blueprint, render_template

mod = Blueprint('wordcounter', __name__, url_prefix='/<lang_code>/wordcounter')

"""
@app.route('/', subdomain='wordcounter')
def index():
	return render_template('wordcounter/index.html')
"""
@mod.route('/')
def index():
	return render_template('wordcounter/index.html')