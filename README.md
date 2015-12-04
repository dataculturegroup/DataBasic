# DataBasic

DataBasic is a suite of web-based data literacy tools and accompanying hands-on activities for journalists, data journalism classrooms and community advocacy groups.

The suite include:

* **WTFcsv**: A web application that takes as input a CSV file and returns a summary of the fields, their data type, their range, and basic descriptive statistics. This is a prettier version of R’s “summary” command and aids at the outset of the data analysis process.
* **WordCounter**: A basic word counting tool that takes unstructured text as input and returns word frequency, bigrams (two-word phrases) and trigrams (three-word phrases)
* **SameDiff**: A tool that compares two text files to show words in common, and words that make each unique.

# Developers

DataBasic is a Python 2.7.10 [Flask](https://github.com/mitsuhiko/flask) app.

## Installation

**1.** Clone this repository and cd into it.
```
git clone https://github.com/c4fcm/DataBasic.git
cd DataBasic
```

You will need to register the app with Google. To do that, create a project in the [Google Developers Console](https://console.developers.google.com/project/_/apiui/credential) and copy the credentials into `config/google-credentials.json`.

**2.** Run the installation script. You will be prompted to install virtualenv if you haven't already.
```
sudo bash install.sh
```

On Ubuntu you might need to do this:
```
sudo apt-get install libblas-dev liblapack-dev libatlas-base-dev libamd2.2.0 libblas3gf libc6 libgcc1 libgfortran3 liblapack3gf libumfpack5.4.0 libstdc++6 build-essential gfortran python-all-dev libatlas-base-dev
```

Also you probably want to do `apt-get install python-numpy` and modify your virtualenv with `virtualenv VIRTUALENV_DIR --system-site-packages`.

On OSX you might need to do this:
```
STATIC_DEPS=true pip install lxml
```

**3.** Start the app. Run this script and then go to localhost:5000 in your browser
```
bash start.sh
```

**4.** (Optional) to add sample data, create a directory in the root called `sample-data`. Then in `config/sample-data.json` specify the paths and which tools should use them.

If after running you get an exception involving sassutils/SassMiddleware, [make sure your C++ compiler is up to date](https://github.com/sass/libsass#readme)

**5.** On an ubuntu server, you might need to compile the sass by hand: `python setup.py build_sass`

## Translating
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
