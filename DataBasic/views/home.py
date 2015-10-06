from flask import Blueprint, render_template

mod = Blueprint('home', __name__, url_prefix='/<lang_code>')

@mod.route('/')
def index():
	return render_template('home/index.html')
