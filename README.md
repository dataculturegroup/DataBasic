DataBasic
=========

DataBasic is a suite of web-based data literacy tools and accompanying hands-on activities for journalists, data journalism classrooms and community advocacy groups.

The suite include:

* **WTFcsv**: A web application that takes as input a CSV file and returns a summary of the fields, their data type, their range, and basic descriptive statistics. This is a prettier version of R’s “summary” command and aids at the outset of the data analysis process.
* **WordCounter**: A basic word counting tool that takes unstructured text as input and returns word frequency, bigrams (two-word phrases) and trigrams (three-word phrases)
* **SameDiff**: A tool that compares two text files to show words in common, and words that make each unique.
* **ConnectTheDots**: A network analysis tool that takes an edgelist and turns it into a graph/table of nodes.

Installation
------------

DataBasic is a Python 2.7.10 [Flask](https://github.com/mitsuhiko/flask) app.

**1.** Clone this repository and cd into it.
```
git clone https://github.com/c4fcm/DataBasic.git
cd DataBasic
```

**2.** Copy `config/development.py.template` to `config/development.py` and enter your settings.

**3.** Create a venv and install the requirements:
```
pip install -r requirements.txt
```

**4.** 
To develop on OSX, like we do, you might need to do this:
```
STATIC_DEPS=true pip install lxml
```

**5.** Start the app. Run this and then go to http://localhost:8000 in your browser:
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

Upgrading
---------

If we've changed the document structures at all, when updating you'll want to remove all the 
sample data so it gets regenerated:

```
python dbutils.py -rm-samples
```

Translating
-----------

We have built DataBasic to support multiple langauges in the user interface.

### Setup
```
$ bash translations-init-RUN-ONLY-ONCE.sh
```
This initializes the translation files. You should only do this once or it'll erase your existing .po files that have translations.

### Add Language 
```
$ bash translations-add-language.sh [LANGUAGE ARGUMENT]
```
Run the above bash command for each language you want the app to support (such as "es", "de", "hu"). This will create a translations directory and a PO file for that language.

### Updating
```
$ bash translations-update.sh
```
This command extracts all items for translation from the app. Each time you add a new bit of text you need to run this comment. Then translate the .po file. If any translations in the .po are marked fuzzy, check them to for accuracy and then remove 'fuzzy.'
```
$ bash translations-compile.sh [LANGUAGE ARGUMENT]
```
This command compiles the translations from the .po files into binary form. You need to run this every time you update a .po file. Then restart the app.

Help us translate Databasic into French!!
-----------

There are three files that we need help translating. Each is a Google Doc that you can type directly into for translation.
- [Databasic software interface](https://docs.google.com/document/d/1J1UCN-UlrydKebdd6TAvR8sIbsyxeVcDfpgYiW0Fq9E/edit)
- [Databasic activity guides](https://docs.google.com/document/d/1gy81vilACpDDqF2a6JEniQxB82mNMu-eWe8Za0sBoMQ/edit#) 
- [Databasic video subtitles](https://docs.google.com/document/d/1ctTQxhkHCtEnRVMHpSs455e1yVXy_p9NuWJ6S6JKFcc/edit)
