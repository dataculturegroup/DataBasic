
# have to move back a dir because in development, Flask is also loading the config in instance/
# for production, in DataBasic/__init__.py set instance_relative_config to False
# and update these paths

# linux / os x:
export APP_CONFIG_FILE=../config/development.py

# windows:
# set APP_CONFIG_FILE=..\config\development.py

alias activate=". venv/bin/activate"
redis-server & celery -A databasic worker --app=databasic.celeryapp --loglevel=debug & python run.py
ps auxww | grep 'celery worker' | awk '{print $2}' | xargs kill -9
redis-cli shutdown