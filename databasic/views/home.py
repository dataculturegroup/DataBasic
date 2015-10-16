from flask import Blueprint, render_template

mod = Blueprint('home', __name__, url_prefix='/<lang_code>', template_folder='../templates/home')

@mod.route('/')
def index():
	return render_template('index.html')
