import json
from werkzeug import secure_filename
from flask_wtf import Form
from flask_wtf.file import FileField
from wtforms import StringField, BooleanField, RadioField, SelectField
from wtforms.widgets import TextArea, TextInput, CheckboxInput
from wtforms.validators import Length, Regexp, Optional, Required, URL

class PasteForm(object):
	area = StringField(
		u'Text',
		validators=[Required(), Length(min=1)], 
		widget=TextArea()) 
	
	def __init__(self, default_text=''):
		super(PasteForm, self).__init__()
		self.area.default = default_text # not working rn

class UploadForm(object):
	upload = FileField(
		u'Upload file',
		# validators=[Regexp(r'^.*\.(txt|docx)$')])
		validators=[Required()])

class SampleForm(object):
	sample = SelectField(
		u'Sample')

	def __init__(self, tool):
		super(SampleForm, self).__init__()
		self.get_samples(tool)

	def get_samples(self, tool):
		lookup = json.load(open('config/sample-data.json'))
		texts = []
		for text in lookup:
			if tool in text['modules']:
				texts.append((text['source'], text['title']))
		self.sample.choices = texts

class LinkForm(object):
	link = StringField(
		u'Link to spreadsheet',
		validators=[URL()],
		widget=TextInput())

class WordCounterForm(object):
	ignore_case = BooleanField(
		u'Ignore case', 
		widget=CheckboxInput(), 
		default=True)
	ignore_stopwords = BooleanField(
		u'Ignore stopwords',
		widget=CheckboxInput(), 
		default=True)

class WordCounterPaste(PasteForm, WordCounterForm, Form):
	def __init__(self, default_text=''):
		super(WordCounterPaste, self).__init__(default_text)

class WordCounterUpload(UploadForm, WordCounterForm, Form):
	pass

class WordCounterSample(SampleForm, WordCounterForm, Form):
	def __init__(self, tool):
		super(WordCounterSample, self).__init__(tool)

class WTFCSVPaste(PasteForm, Form):
	def __init__(self, default_text=''):
		super(WTFCSVPaste, self).__init__(default_text)

class WTFCSVUpload(UploadForm, Form):
	pass

class WTFCSVLink(LinkForm, Form):
	pass
