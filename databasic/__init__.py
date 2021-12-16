import codecs
import json
import os
import sys
import logging.handlers
from flask_mail import Mail
from flask import Flask, g, redirect, request, abort, send_from_directory
from flask_assets import Environment, Bundle
from flask_babel import Babel
from sassutils.wsgi import SassMiddleware
import nltk

import databasic.logic.filehandler
import databasic.logic.db
import databasic.logic.oauth


VALID_LANGUAGES = ('es', 'en', 'en_GB','en_CY', 'pt', 'da', 'cy')
NLTK_STOPWORDS_BY_LANGUAGE = {
    'es': 'spanish',
    'en': 'english',
    'en_CY': 'welsh_english',
    'pt': 'portuguese',
    'da': 'danish',
    'cy': 'welsh'
}

CONFIG_DIR_NAME = 'config'

ENV_APP_MODE = 'APP_MODE'   # the environment variable holding which settings file to load (just the name)

APP_MODE_DEV = "development"
APP_MODE_PRODUCTION = "production"

HOST = ""

app_mode = os.environ.get(ENV_APP_MODE, APP_MODE_DEV)

# ATTEMPTING UNICODE FIX
#reload(sys)
#sys.setdefaultencoding('utf-8')


if app_mode is None:
    logging.error("missing necessary environment variable %s (%s,%s)" % (ENV_APP_MODE, APP_MODE_DEV,
                                                                         APP_MODE_PRODUCTION))
    sys.exit()


def get_base_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_config_dir():
    return os.path.join(get_base_dir(), CONFIG_DIR_NAME)


# init the logging config
if app_mode == APP_MODE_DEV:
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
else:
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__file__)
logger.info("------------------------------------------------------------------------------")
logger.info("Starting DataBasic in %s mode" % app_mode)

# Initialize the app
app = Flask(__name__, instance_relative_config=False)
app.config[ENV_APP_MODE] = app_mode
config_var_names = ['SECRET_KEY', 'MONGODB_URL', 'MONGODB_NAME', 'SAMPLE_DATA_SERVER', 'GOOGLE_ANALYTICS_ID',
                    'GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', 'OAUTH_REDIRECT_URI', 'MAX_CONTENT_LENGTH',
                    'MAIL_SERVER', 'MAIL_USERNAME', 'MAIL_PASSWORD']
if app_mode == APP_MODE_DEV:
    import config.development
    logger.info('Loading config from %s:' % APP_MODE_DEV)
    app.config.from_object(config.development)
    for var_name in config_var_names:
        logger.info('  %s=%s' % (var_name, app.config.get(var_name)))
elif app_mode == APP_MODE_PRODUCTION:
    logger.info('Loading config from environment variables')
    for var_name in config_var_names:
        try:
            app.config[var_name] = int(os.environ.get(var_name, None)) if var_name in ['MAX_CONTENT_LENGTH'] else os.environ.get(var_name, None)
        except TypeError:
            logger.error("Looks like you have not set the %s environment variable!" % var_name)
        if app.config[var_name] is None:
            logger.error("Looks like you have not set the %s environment variable!" % var_name)
else:
    logger.error("invalid APP_MODE of %s" % app_mode)

# Setup sass auto-compiling
app.wsgi_app = SassMiddleware(app.wsgi_app, {
    'databasic': ('static/sass', 'static/css', '/static/css')
})

# Set up bundles
assets = Environment(app)
js_bundle = Bundle('js/lib/jquery.js', 'js/lib/jquery.validate.min.js', 'js/lib/additional-methods.min.js',
                   'js/lib/bootstrap.min.js', 'js/lib/Gettext.js',
                   filters='jsmin', output='gen/packed.js')
assets.register('js_base', js_bundle)
js_tool = Bundle('js/lib/d3.min.js', 'js/lib/d3.layout.cloud.js', 'js/lib/d3.tip.js', 'js/lib/underscore.min.js',
                 'js/lib/jquery.flip.min.js', 'js/lib/highcharts.src.js',
                 filters='jsmin', output='gen/packed_tool.js')
assets.register('js_tool', js_tool)
js_ctd = Bundle('js/lib/d3.min.js', 'js/lib/saveSvgAsPng.js', 'js/lib/underscore.min.js',
                'js/lib/jquery.floatThead-slim.min.js', 'js/connectthedots.js',
                filters='jsmin', output='gen/packed_ctd.js')
assets.register('js_ctd', js_ctd)
css_bundle = Bundle('css/bootstrap.css', 'css/font-awesome.min.css',
                    filters='cssmin', output='gen/packed.css')
assets.register('css_base', css_bundle)

# initialize helper components
babel = Babel(app)
mongo = databasic.logic.db.MongoHandler(app.config.get('MONGODB_URL'), app.config.get('MONGODB_NAME'))
databasic.logic.oauth.init(app.config.get('GOOGLE_CLIENT_ID'), app.config.get('GOOGLE_CLIENT_SECRET'),
                 app.config.get('OAUTH_REDIRECT_URI'))
databasic.logic.filehandler.load_sample_file()
local_nltk_path = os.path.join(get_base_dir(), 'nltk_data')
logger.info("Adding nltk path %s", local_nltk_path)
nltk.data.path.append(local_nltk_path)

try:
    mail = Mail()
    mail_config = {  # @see https://pythonhosted.org/Flask-Mail/
        'MAIL_SERVER': app.config.get('MAIL_SERVER'),
        'MAIL_USERNAME': app.config.get('MAIL_USERNAME'),
        'MAIL_PASSWORD': app.config.get('MAIL_PASSWORD'),
        'MAIL_PORT': 465,
        'MAIL_USE_SSL': 1,
    }
    app.config.update(mail_config)
    mail.init_app(app)
    logger.info('Mail configured, from {}'.format(app.config.get('MAIL_USERNAME')))
except Exception as e:
    logger.info("No mail configured")

# uncomment to use toolbar (this slows the app down quite a bit)
# toolbar = DebugToolbarExtension(app)


@app.before_request
def before():
    
    if request.view_args and 'lang_code' in request.view_args:
        if request.view_args['lang_code'] not in VALID_LANGUAGES:
            return abort(404)  # bail on invalid language
        g.current_lang = request.view_args['lang_code']
        logger.info("Current language is %s" % g.get('current_lang'))

        g.max_file_size_bytes = int(app.config.get('MAX_CONTENT_LENGTH'))
        g.max_file_size_mb = (g.max_file_size_bytes / 1024 / 1024)
        # loads the translation files to be used for client-side validation
        if 'en' not in g.current_lang:
            with codecs.open(os.path.join(get_base_dir(), 'databasic/translations', g.current_lang,
                                          'LC_MESSAGES/messages.json'), 'r', 'utf-8') as f:
                g.messages = json.dumps(f.read())

        request.view_args.pop('lang_code')


@babel.localeselector
def get_locale():
    logger.info("Current language from locale selector is %s " %  g.get('current_lang'))
    #Welsh site defaults to Welsh English
    if g.get('current_lang') is None:
        if ('cymru' in request.host) and ((g.get('current_lang') != "en_CY") and (g.get('current_lang') != "cy")):
            g.current_lang = "en_CY"
            logger.info("Setting default language to Welsh English")
    return g.get('current_lang', request.accept_languages.best_match(VALID_LANGUAGES, 'en'))


@app.route('/')
def index():
    return redirect('/' + get_locale())


@app.route('/wordcounter')
def wordcounter():
    return redirect('/' + get_locale() + '/wordcounter')


@app.route('/wordcounter/<stuff>')
def wordcounter_with_stuff(stuff):
    return redirect('/' + get_locale() + '/wordcounter/'+stuff)


@app.route('/samediff')
def samediff():
    return redirect('/' + get_locale() + '/samediff')


@app.route('/samediff/<stuff>')
def samediff_with_stuff(stuff):
    return redirect('/' + get_locale() + '/samediff/'+stuff)


@app.route('/wtfcsv')
def wtfcsv():
    return redirect('/' + get_locale() + '/wtfcsv')


@app.route('/wtfcsv/<stuff>')
def wtfcsv_with_stuff(stuff):
    return redirect('/' + get_locale() + '/wtfcsv/'+stuff)


@app.route('/auth')
def auth():
    if 'code' not in request.args:
        logger.debug('permission was not granted')
    else:
        logger.debug(request.args['code'])
        databasic.logic.oauth.authorize(request.args['code'])
    return redirect(databasic.logic.oauth.redirect_to())


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'img', 'icons'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')


logger.debug("Importing views...")
from databasic.views import home
from databasic.views import samediff
from databasic.views import wordcounter
from databasic.views import wtfcsv
from databasic.views import connectthedots
from databasic.views import culture
logger.debug("  done")


logger.debug("Registering blueprints...")
app.register_blueprint(home.mod)
app.register_blueprint(samediff.mod)
app.register_blueprint(wordcounter.mod)
app.register_blueprint(wtfcsv.mod)
app.register_blueprint(connectthedots.mod)
app.register_blueprint(culture.mod)
logger.debug("  done")
