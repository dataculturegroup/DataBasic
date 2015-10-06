from flask import Blueprint, render_template

mod = Blueprint('wtfcsv', __name__, url_prefix='/<lang_code>/wtfcsv')

@mod.route('/')
def index():
	return render_template('wtfcsv/index.html')