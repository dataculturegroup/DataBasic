from flask import Flask, Blueprint, g, redirect, request, abort
from flask_debugtoolbar import DebugToolbarExtension
from flask.ext.babel import Babel
from logic import OAuthHandler
# from logic.mongohandler import MongoHandler

app = Flask(__name__, instance_relative_config=True)

# Load the default configuration
app.config.from_object('config.default')

# Load the configuration from the instance folder
app.config.from_pyfile('config.py')

# Load the file specified by the APP_CONFIG_FILE environment variable
# Variables defined here will override those in the default configuration
app.config.from_envvar('APP_CONFIG_FILE')

babel = Babel(app)
# uncomment to use toolbar (this slows the app down quite a bit)
# toolbar = DebugToolbarExtension(app)

@app.before_request
def before():
	if request.view_args and 'lang_code' in request.view_args:
		if request.view_args['lang_code'] not in ('es', 'en'):
			return abort(404) # bail on invalid language
		g.current_lang = request.view_args['lang_code']
		request.view_args.pop('lang_code')

@babel.localeselector
def get_locale():
	return g.get('current_lang', 'en')

@app.route('/')
def index():
	# m = MongoHandler(app.config['HOST'], app.config['PORT'])
	return redirect('/' + get_locale())

@app.route('/auth')
def auth():
	if 'code' not in request.args:
		print 'permission was not granted'
	else:
		print request.args['code']
		OAuthHandler.authorize(request.args['code'])
	return redirect(OAuthHandler.redirect_to())

from DataBasic.views import home
from DataBasic.views import samediff
from DataBasic.views import wordcounter
from DataBasic.views import wtfcsv
app.register_blueprint(home.mod)
app.register_blueprint(samediff.mod)
app.register_blueprint(wordcounter.mod)#, subdomain='wordcounter')
app.register_blueprint(wtfcsv.mod)

