import os, ConfigParser, ntpath, logging, logging.handlers, sys
import logging, os, sys, ntpath, logging.handlers
from flask import Flask, Blueprint, g, redirect, request, abort
from flask.ext.assets import Environment, Bundle
from flask.ext.babel import Babel
from flask_debugtoolbar import DebugToolbarExtension
#from flask.ext.mail import Mail
from sassutils.wsgi import SassMiddleware
from babel.support import LazyProxy

import logic.db, logic.oauth, config.development

CONFIG_DIR_NAME = 'config'

ENV_APP_MODE = 'APP_MODE'   # the environment variable holding which settings file to load (just the name)

APP_MODE_DEV = "development"
APP_MODE_PRODUCTION = "production"

app_mode = os.environ.get(ENV_APP_MODE, None)
if(app_mode is None):
    logging.error("missing necessary environment variable %s (%s,%s,%s)" % 
        (ENV_APP_MODE,APP_MODE_DEV,APP_MODE_PRODUCTION) )
    sys.exit()

def get_base_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_config_dir():
    return os.path.join(get_base_dir(),CONFIG_DIR_NAME)

# init the logging config
root_logger = logging.getLogger('')
root_logger.setLevel(logging.DEBUG)
if app_mode == APP_MODE_DEV:
    log_file_path = os.path.join(get_base_dir(),'logs', app_mode+'.log')
    handler = logging.handlers.RotatingFileHandler(log_file_path, maxBytes=5242880, backupCount=10)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
logging.info("------------------------------------------------------------------------------")
logging.info("Starting DataBasic in %s mode" % app_mode)

# Initialize the app
app = Flask(__name__, instance_relative_config=False)
app.config[ENV_APP_MODE] = app_mode
config_var_names = ['SECRET_KEY','MONGODB_URL','MONGODB_NAME','GOOGLE_CLIENT_ID','GOOGLE_CLIENT_SECRET','GOOGLE_ANALYTICS_ID','SAMPLE_DATA_SERVER']
if app_mode == APP_MODE_DEV:
    logging.info('Loading config from %s:' % (APP_MODE_DEV))
    app.config.from_object(config.development)
    for var_name in config_var_names:
        logging.info('  %s=%s' % (var_name,app.config.get(var_name)))
elif app_mode == APP_MODE_PRODUCTION:
    logging.info('Loading config from environment variables')
    for var_name in config_var_names:
        app.config[var_name] = os.environ.get(var_name, None)
        if app.config[var_name] is None:
            logging.error("Looks like you have not set the %s environment variable!" % var_name)
else:
    logging.error("invalid APP_MODE of %s" % app_mode)

# Setup sass auto-compiling
app.wsgi_app = SassMiddleware(app.wsgi_app, {
    'databasic': ('static/sass', 'static/css', '/static/css')
})

# Set up bundles
assets = Environment(app)
js_bundle = Bundle('js/lib/jquery.js', 'js/lib/jquery.validate.min.js', 'js/lib/additional-methods.min.js', 'js/lib/bootstrap.min.js',
	filters='jsmin', output='gen/packed.js')
assets.register('js_all', js_bundle)

babel = Babel(app)
mongo = logic.db.MongoHandler(app.config.get('MONGODB_URL'),app.config.get('MONGODB_NAME'))
logic.oauth.init(app.config.get('GOOGLE_CLIENT_ID'),app.config.get('GOOGLE_CLIENT_SECRET'))

#mail = Mail(app)
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
        logic.oauth.authorize(request.args['code'])
    return redirect(logic.oauth.redirect_to())

from databasic.views import home
from databasic.views import samediff
from databasic.views import wordcounter
from databasic.views import wtfcsv
app.register_blueprint(home.mod)
app.register_blueprint(samediff.mod)
app.register_blueprint(wordcounter.mod)#, subdomain='wordcounter')
app.register_blueprint(wtfcsv.mod)

