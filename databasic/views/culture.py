import feedparser, logging, re, time
from flask import Blueprint, render_template

mod = Blueprint('culture', __name__, url_prefix='/<lang_code>/culture', template_folder='../templates/culture')

logger = logging.getLogger(__name__)

@mod.route('/', methods=('GET', 'POST'))
def index():

    return render_template('culture/culture.html')