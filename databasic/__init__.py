import os, ConfigParser, ntpath, logging, logging.handlers

ENV_CONFIG_FILE_VAR = 'APP_CONFIG_FILE'	# the environment variable holding path to app config file
ENV_CONFIG_FILE_VAR_MISSING_VAL = 'NOTSET' # the default val indicating the user needs to set the env config var

CONFIG_DIR_NAME = 'config'

def get_base_dir():
	return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_settings_config_file_path():
    config_file_path = os.path.join(get_base_dir(),CONFIG_DIR_NAME,'settings.config')
    return config_file_path

def get_settings_py_file_path():
    config_file_path = os.path.join(get_base_dir(),CONFIG_DIR_NAME,'settings.py')
    return config_file_path

def get_config_file_path():
	config_file_path = os.environ.get(ENV_CONFIG_FILE_VAR, ENV_CONFIG_FILE_VAR_MISSING_VAL)
	# bail if the config file is not specified
	if config_file_path is ENV_CONFIG_FILE_VAR_MISSING_VAL:
		print("ERROR! missing necessary environment variable %s" % ENV_CONFIG_FILE_VAR)
		print("Set it with something like this and try again")
		print("  export "+ENV_CONFIG_FILE_VAR+"=/abs/path/to/DataBasic/config/development.py")
		sys.exit()
	return config_file_path

# init the logging config
app_mode = os.path.splitext(ntpath.basename(get_config_file_path()))[0]
log_file_path = os.path.join(get_base_dir(),'logs', app_mode+'.log')
handler = logging.handlers.RotatingFileHandler(log_file_path, maxBytes=5242880, backupCount=10)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root_logger = logging.getLogger('')
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(handler)
logging.info("Starting DataBasic in %s mode" % app_mode)

# load the settings
settings = ConfigParser.ConfigParser()
settings.read(get_settings_config_file_path())
