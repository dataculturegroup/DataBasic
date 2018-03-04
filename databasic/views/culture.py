# coding=utf-8
import logging
import random
from flask import Blueprint, render_template

mod = Blueprint('culture', __name__, url_prefix='/<lang_code>/culture', template_folder='../templates/culture')

logger = logging.getLogger(__name__)


@mod.route('/', methods=('GET', 'POST'))
def index():
    # TODO: move to .json file for easier maintenance
    quotes = [
        {
            'text': u"The Data Culture Project allowed us to <b>change a mindset about data",
            'author': u"Andrés Felipe Vera Ramírez, El Mundo/Radio Clarin"
        },
        {
            'text': u"The DCP program helped us look at data in a different way",
            'author': u"Jennifer Connolly, Junior Achievement of Western Massachusetts"
        },
        {
            'text': u"This program was accessible to people of all levels",
            'author': u"Jennifer Connolly, Junior Achievement of Western Massachusetts"
        },
        {
            'text': u"The tools were accessible and the pacing of the workshops was great",
            'author': u"Michael Morisy, MuckRock"
        },
        {
            'text': u"Folks who don’t typically use data in their day-to-day roles engaged in the sessions",
            'author': u"Michael Smith Foundation for Health Research"
        },
    ]
    return render_template('culture.html', featured_quote=random.choice(quotes))


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
