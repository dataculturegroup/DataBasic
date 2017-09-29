import logging
from flask import Blueprint, render_template, request, jsonify

from databasic.forms import CultureFeedbackForm, CultureSketchAStory, CultureAskQuestions, CultureConvinceMe
from databasic.mail import send_email, DEFAULT_SENDER

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


@mod.route('/build-a-sculpture')
def sculpture():
    form = CultureFeedbackForm()
    return render_template('sculpture.html', form=form, tool_name='sculpture')


@mod.route('/feedback', methods=['POST', 'GET'])
def feedback():
    try:
        feedback = request.form['feedback']
        from_email = request.form['email']
        # now send an email
        content = """
    Hi,
    
    Thanks for your feedback!  We'll try to get back to you soon.
    
    Feedback:
    """
        content += feedback
        send_email(DEFAULT_SENDER, [from_email, 'feedback@databasic.io'],
                             "Data Culture Project: Feedback Received", content)
    except Exception as e:
        logger.error("email failed to send")
        logger.exception(e)
        return jsonify({'success': False})
    return jsonify({'success': True})
