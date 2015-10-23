import os
import json
from werkzeug import secure_filename
from flask.ext.babel import lazy_gettext as _
from flask_wtf import Form
from flask_wtf.file import FileField
from wtforms import StringField, BooleanField, RadioField, SelectField
from wtforms.widgets import TextArea, TextInput, CheckboxInput
from wtforms.validators import Length, Regexp, Optional, Required, URL, Email

class PasteForm(object):
	area = StringField(
		_('Text'),
		validators=[Required()], 
		widget=TextArea()) 
	
	def __init__(self, default_text=''):
		super(PasteForm, self).__init__()
		self.area.default = default_text # not working rn

class UploadForm(object):
	upload = FileField(
		_('Upload file'),
		# validators=[Regexp(r'^.*\.(txt|docx)$')])
		validators=[Required()])

class SampleForm(object):
	sample = SelectField(
		_('Sample'))

	def __init__(self, tool):
		super(SampleForm, self).__init__()
		self.get_samples(tool)

	def get_samples(self, tool):
		if os.path.isdir('sample-data') and os.path.exists('config/sample-data.json'):
			lookup = json.load(open('config/sample-data.json'))
			texts = []
			for text in lookup:
				if tool in text['modules']:
					texts.append((text['source'], text['title']))
			self.sample.choices = texts
		else:
			self.sample.choices = []

class LinkForm(object):
	field_flags = ('url',)
	link = StringField(
		_('Link to spreadsheet'),
		validators=[URL(), Required()],
		widget=TextInput())

'''
Word-Counter forms
'''

class WordCounterForm(object):
	ignore_case = BooleanField(
		_('Ignore case'), 
		widget=CheckboxInput(), 
		default=True)
	ignore_stopwords = BooleanField(
		_('Ignore stopwords'),
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

'''
WTFcsv forms
'''

class WTFCSVPaste(PasteForm, Form):
	def __init__(self, default_text=''):
		super(WTFCSVPaste, self).__init__(default_text)

class WTFCSVUpload(UploadForm, Form):
	pass

class WTFCSVLink(LinkForm, Form):
	pass

'''
SameDiff forms
'''

class SameDiffForm(object):
	email = StringField(
		_('Email'),
		validators=[Required(), Email()],
		widget=TextInput())

class SameDiffUpload(UploadForm, SameDiffForm, Form):
	pass
