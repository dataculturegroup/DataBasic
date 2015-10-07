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

**2.** Install and run [virtualenv](http://virtualenv.readthedocs.org/en/latest/). This allows us to run the app on our localhost.
```
pip install virtualenv
virtualenv venv
source venv/bin/activate
```

**3.** Install dependencies.

Install Python packages using [pip](https://pip.pypa.io/en/latest/installing/)
```
[sudo] pip install -r requirements.txt
```
Then install the NLTK libraries we're using
```
python -m nltk.downloader punkt
python -m nltk.downloader stopwords
```

**4.** Generate a secret key in Terminal.
```
$ python
>> import os
>> os.urandom(24)
'/secret/key/to/copy'
>> exit()
```

Copy + paste this key into `instance/config.py`. You will have to create this file because git ignores the `instance/` directory. This is also where you should store any credentials.
```
# instance/config.py
SECRET_KEY = '/secret/key/to/copy'
```

**5.** Start the app! Run this shell script and then go to localhost:5000 in your browser
```
bash start.sh
```

## Run

After installation, you can run the app by activating the virtual environment and starting the server. 

```
cd DataBasic
source venv/bin/activate
bash start.sh
```
