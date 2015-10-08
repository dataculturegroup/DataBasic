from werkzeug import secure_filename
from flask_wtf import Form
from flask_wtf.file import FileField
from wtforms import StringField, BooleanField
from wtforms.widgets import TextArea, TextInput, CheckboxInput
from wtforms.validators import Length, Regexp, Optional, URL

class WordCountForm(Form):
	area = StringField(
		u'Text',
		[Optional(), Length(min=1)], 
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
	upload = FileField(u'Upload file', [Optional(), Regexp(u'^.*\.(txt|docx)$')])

class WTFCSVForm(Form):
	area = StringField(
		u'Paste CSV',
		[Optional()],
		widget=TextArea(),
		default='name, shirt_color, siblings\nRahul, blue, 1\nCatherine, red, 2')
	upload = FileField(
		u'Upload file',
		[Optional(),
		Regexp(u'^.*\.csv$')])
	link = StringField(
		u'Link to spreadsheet',
		[Optional(), URL()],
		widget=TextInput())