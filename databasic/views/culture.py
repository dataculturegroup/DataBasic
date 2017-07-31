import logging, os
from collections import OrderedDict
from databasic import mongo, get_base_dir
from databasic.forms import SameDiffUpload, SameDiffSample
from databasic.logic import filehandler
from databasic.logic import textanalysis
from flask import Blueprint, render_template, request, redirect, g, abort, send_from_directory
from flask.ext.babel import lazy_gettext as _

mod = Blueprint('culture', __name__, url_prefix='/<lang_code>/culture', template_folder='../templates/culture')

logger = logging.getLogger(__name__)

@mod.route('/', methods=('GET', 'POST'))
def index():

    return render_template('culture/culture.html')