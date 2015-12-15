import logging
from flask import Blueprint, render_template

mod = Blueprint('home', __name__, url_prefix='/<lang_code>', template_folder='../templates/home')

logger = logging.getLogger(__name__)

@mod.route('/')
def index():
	return render_template('index.html')
