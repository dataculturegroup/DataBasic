from ..forms import WTFCSVForm
from ..logic import wtfcsvstat
from flask import Blueprint, render_template, request

mod = Blueprint('wtfcsv', __name__, url_prefix='/<lang_code>/wtfcsv', template_folder='../templates/wtfcsv')

@mod.route('/', methods=('GET', 'POST'))
def index():

	form = WTFCSVForm()

	if request.method == 'POST':
		pass

	return render_template('wtfcsv.html', form=form)