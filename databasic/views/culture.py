import logging
from flask import Blueprint, render_template

mod = Blueprint('culture', __name__, url_prefix='/<lang_code>/culture', template_folder='../templates/culture')

logger = logging.getLogger(__name__)


@mod.route('/', methods=('GET', 'POST'))
def index():
    return render_template('culture.html')


@mod.route('/sketch-a-story')
def sketch():
    return render_template('sketch.html')


@mod.route('/convince-me')
def convince():
    return render_template('convince.html')


@mod.route('/ask-questions')
def questions():
    return render_template('questions.html')


@mod.route('/build-a-sculpture')
def sculpture():
    return render_template('sculpture.html')


@mod.route('/connections')
def connections():
    return render_template('connections.html')


@mod.route('/testimonials')
def testimonials():
    return render_template('testimonials.html')
