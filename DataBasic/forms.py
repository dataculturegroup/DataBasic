from werkzeug import secure_filename
from flask_wtf import Form
from flask_wtf.file import FileField
from wtforms import StringField
from wtforms import BooleanField
from wtforms.widgets import TextArea
from wtforms.widgets import CheckboxInput
from wtforms.validators import Length

class WordCountForm(Form):
	area = StringField(
		u'Text',
		[Length(min=1)], 
		widget=TextArea(), 
		default='I am Sam\nSam I am\nThat Sam-I-am!\nThat Sam-I-am!\nI do not like that Sam-I-am!\nDo you like \ngreen eggs and ham?\nI do not like them, Sam-I-am.\nI do not like\ngreen eggs and ham.\nWould you like them \nhere or there?\nI would not like them\nhere or there.\nI would not like them anywhere.')
	ignore_case = BooleanField(
		u'Ignore case', 
		widget=CheckboxInput(), 
		default=True)
	ignore_stopwords = BooleanField(
		u'Ignore stopwords', 
		widget=CheckboxInput(), 
		default=True)
