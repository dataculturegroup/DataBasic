DataBasic
=========

DataBasic is a suite of web-based data literacy tools and accompanying hands-on activities for journalists, data journalism classrooms and community advocacy groups.

The suite include:

* **WTFcsv**: A web application that takes as input a CSV file and returns a summary of the fields, their data type, their range, and basic descriptive statistics. This is a prettier version of R’s “summary” command and aids at the outset of the data analysis process.
* **WordCounter**: A basic word counting tool that takes unstructured text as input and returns word frequency, bigrams (two-word phrases) and trigrams (three-word phrases)
* **SameDiff**: A tool that compares two text files to show words in common, and words that make each unique.

Installation
------------

DataBasic is a Python 2.7.10 [Flask](https://github.com/mitsuhiko/flask) app.

**1.** Clone this repository and cd into it.
```
git clone https://github.com/c4fcm/DataBasic.git
cd DataBasic
```

**2.** Edit the `config/development.py` file and enter your settings. You will need to register the app with Google. To do that, create a project in the [Google Developers Console](https://console.developers.google.com/project/_/apiui/credential) and copy the credentials into `config/development.py`.

**3.** Create a venv and install the requirements `pip install -r requirements`

**4.** 
To develop on OSX, like we do, you might need to do this:
```
STATIC_DEPS=true pip install lxml
```

**5.** Start the app. Run this and then go to localhost:5000 in your browser:
```
gunicorn databasic:app
```

Deploying
---------

### Heroku

For deploying to Heroku, install and use the [scipy buildpack](https://github.com/thenovices/heroku-buildpack-scipy).

On your dyno make sure you set up an environment variable for each property in the `config/development.py` file.

### Ubuntu

You'll need to do some extra stuff on Ubuntu to get all the libraries working:

```
sudo apt-get install libblas-dev liblapack-dev libatlas-base-dev libamd2.2.0 libblas3gf libc6 libgcc1 libgfortran3 liblapack3gf libumfpack5.4.0 libstdc++6 build-essential gfortran python-all-dev libatlas-base-dev
```

Also you probably want to do `apt-get install python-numpy` and modify your virtualenv with `virtualenv VIRTUALENV_DIR --system-site-packages`.

If after running you get an exception involving sassutils/SassMiddleware, [make sure your C++ compiler is up to date](https://github.com/sass/libsass#readme)

You probably will need to compile the sass by hand: `python setup.py build_sass`

Translating
-----------

We have built DataBasic to support multiple langauges in the user interface.

### Setup
```
$ bash init-translations.sh
```

### Updating
```
$ bash update-translations.sh
```
Translate the .po file. If the .po is marked fuzzy, remove 'fuzzy.'
```
$ bash compile-translations.sh
```
