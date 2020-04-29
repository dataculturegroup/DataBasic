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
            'text': "The Data Culture Project allowed us to <b>change a mindset about data",
            'author': "Andrés Felipe Vera Ramírez, El Mundo/Radio Clarin"
        },
        {
            'text': "The DCP program helped us <b>look at data in a different way</b>",
            'author': "Jennifer Connolly, Junior Achievement of Western Massachusetts"
        },
        {
            'text': "This program was <b>accessible</b> to people of all levels",
            'author': "Jennifer Connolly, Junior Achievement of Western Massachusetts"
        },
        {
            'text': "The tools were <b>accessible</b> and the pacing of the workshops was great",
            'author': "Michael Morisy, MuckRock"
        },
        {
            'text': "Folks who don’t typically use data in their day-to-day <b>roles engaged in the sessions</b>",
            'author': "Michael Smith Foundation for Health Research"
        },
        {
            'text': "I saw a <b>big change</b> in how our partners treated data",
            'author': "Erika Lapsys, Telluride Foundation"
        },
        {
            'text': "For the first time, the numbers [from our grantees] were <b>consistent</b>",
            'author': "Erika Lapsys, Telluride Foundation"
        },
        {
            'text': "Participants started looking at ... which piece of data is <b>more relevant</b> for which type of stakeholder",
            'author': "Maryna Taran, World Food Programme"
    }
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


@mod.route('/deconstruct-a-dataviz')
def deconstruct():
    return render_template('deconstruct.html')


@mod.route('/make-word-webs')
def word_webs():
    return render_template('word_webs.html')


@mod.route('/connections')
def connections():
    return render_template('connections.html')


@mod.route('/testimonials')
def testimonials():
    return render_template('testimonials.html')


@mod.route('/paper-spreadsheet')
def paper_spreadsheet():
    return render_template('paper_spreadsheet.html')


@mod.route('/storybook')
def storybook():
    return render_template('storybook.html')

@mod.route('/remix')
def remix():
    return render_template('remix.html')
