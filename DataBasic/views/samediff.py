from flask import Blueprint, render_template

mod = Blueprint('samediff', __name__, url_prefix='/<lang_code>/samediff')

@mod.route('/')
def index():
	return render_template('samediff/index.html')

