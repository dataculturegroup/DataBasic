# DataBasic

DataBasic is a suite of focused and simple tools and activities for journalists, data journalism classrooms and community advocacy groups.

Though there are numerous data analysis and visualization tools for novices there are some significant gaps that we have identified through prior research. DataBasic is designed to fill these gaps for people who do not know how to code and provide a low barrier to further learning about data analysis for storytelling.

In the first iteration of this project we will build three tools, develop three training activities and run one workshop with journalists and students for feedback. The three tools include:

* **WTFcsv**: A web application that takes as input a CSV file and returns a summary of the fields, their data type, their range, and basic descriptive statistics. This is a prettier version of R’s “summary” command and aids at the outset of the data analysis process.
* **WordCounter**: A basic word counting tool that takes unstructured text as input and returns word frequency, bigrams (two-word phrases) and trigrams (three-word phrases)
* **SameDiff**: A tool that runs TF-IDF algorithms on two or more corpora in order to compare which words occur with the most frequency and uniqueness.

More importantly, we’ll be providing an introductory video and simple training activities for each tool as a way to scaffold learning about data analysis at the same time as doing it. These activities will include fun datasets to start off with, and introduce vocabulary terms and the algorithms at work behind the scenes.  We strongly believe in building tools for learners, and will be putting those ideas into practice on these tools and activities.

# Developers

DataBasic is a Python 2.7 [Flask](https://github.com/mitsuhiko/flask) app.

## Installation

**1.** Clone this repository and cd into it.
```
git clone https://github.com/c4fcm/DataBasic.git
cd DataBasic
```

**2.** Run the installation script. You will be prompted to install virtualenv if you haven't already.
```
sudo bash install.sh
```

**3.** Start the app. Run this script and then go to localhost:5000 in your browser
```
bash start.sh
```

## Translating
### Setup
```
$ pybabel extract -F config/babel.cfg databasic/ -o databasic/messages.pot
$ pybabel init -i databasic/messages.pot -d databasic/translations -l es
```
Translate the .po file. If the .po is marked fuzzy, remove 'fuzzy.'
```
$ pybabel compile -d databasic/translations
```

### Updating
```
$ pybabel extract -F config/babel.cfg databasic/ -o databasic/messages.pot
$ pybabel update -i databasic/messages.pot -d databasic/translations
```
Translate the .po file. If the .po is marked fuzzy, remove 'fuzzy.'
```
$ pybabel compile -d databasic/translations
```