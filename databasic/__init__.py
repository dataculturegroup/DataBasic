import os, ConfigParser

def get_settings_file_path():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_file_path = os.path.join(current_dir,'../config','settings.config')
    return config_file_path

settings = ConfigParser.ConfigParser()
settings.read(get_settings_file_path())