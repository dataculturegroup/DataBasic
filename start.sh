
# have to move back a dir because in development, Flask is also loading the config in instance/
# for production, in DataBasic/__init__.py set instance_relative_config to False
# and update these paths

# linux / os x:
export APP_MODE=development

# windows:
# set APP_CONFIG_FILE=..\config\development.py

alias activate=". venv/bin/activate"
gunicorn -b 10.25.69.236 -b [::1]:8000 databasic:app --timeout 120 --reload
# wait
# redis-server & celery -A databasic worker --app=databasic.celeryapp --loglevel=debug & python run.py & apid=$!;
# wait;
# while kill -0 $apid; do ps auxww | grep 'celery worker' | awk '{print $2}' | xargs kill -9; done
# redis-cli shutdown
