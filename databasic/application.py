import logging
from flask import Flask, Blueprint, g, redirect, request, abort
from flask.ext.babel import Babel
from flask_debugtoolbar import DebugToolbarExtension
from flask.ext.mail import Mail
from sassutils.wsgi import SassMiddleware
from babel.support import LazyProxy
from logic import oauth
from logic.db import MongoHandler

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__, instance_relative_config=False)

# Load the default configuration
app.config.from_object('config.default')

# Load the configuration from the instance folder
app.config.from_pyfile('../config/settings.py')

# Load the file specified by the APP_CONFIG_FILE environment variable
# Variables defined here will override those in the default configuration
app.config.from_envvar('APP_CONFIG_FILE')

# Setup sass auto-compiling
app.wsgi_app = SassMiddleware(app.wsgi_app, {
	'databasic': ('static/sass', 'static/css', '/static/css')
})

babel = Babel(app)
mongo = MongoHandler(app)
mail = Mail(app)
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
	return redirect('/' + get_locale())

@app.route('/auth')
def auth():
	if 'code' not in request.args:
		print 'permission was not granted'
	else:
		print request.args['code']
		oauth.authorize(request.args['code'])
	return redirect(oauth.redirect_to())

from databasic.views import home
from databasic.views import samediff
from databasic.views import wordcounter
from databasic.views import wtfcsv
app.register_blueprint(home.mod)
app.register_blueprint(samediff.mod)
app.register_blueprint(wordcounter.mod)#, subdomain='wordcounter')
app.register_blueprint(wtfcsv.mod)

