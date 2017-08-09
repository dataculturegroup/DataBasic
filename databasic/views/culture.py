import feedparser, logging, re, time
from collections import OrderedDict
from databasic.forms import CultureForm, CultureSketchAStory, CultureAskQuestions, CultureConvinceMe
from flask import Blueprint, render_template, request

mod = Blueprint('culture', __name__, url_prefix='/<lang_code>/culture', template_folder='../templates/culture')

logger = logging.getLogger(__name__)

@mod.route('/', methods=('GET', 'POST'))
def index():
  return render_template('culture.html', tool_name='culture')

@mod.route('/sketch-a-story')
def sketch():

  form = CultureSketchAStory()

  return render_template('sketch.html', form=form, tool_name='sketch')

@mod.route('/convince-me')
def convince():

  form = CultureConvinceMe()

  return render_template('convince.html', form=form, tool_name='convince')

@mod.route('/ask-questions')
def questions():

  form = CultureAskQuestions()

  return render_template('questions.html', form=form, tool_name='questions')

@mod.route('/feedback', methods=['POST', 'GET'])
def feedback():
  logger.info('what did we get')
  logger.info(request)
  return 'Nice'