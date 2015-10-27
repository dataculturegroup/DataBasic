import os, json
from logic import filehandler
from werkzeug import secure_filename
from flask.ext.babel import lazy_gettext as _
from flask_wtf import Form
from flask_wtf.file import FileField
from wtforms import StringField, BooleanField, RadioField, SelectField, SelectMultipleField
from wtforms.widgets import TextArea, TextInput, CheckboxInput

class PasteForm(object):
	area = StringField(
		_('Text'),
		widget=TextArea()) 
	
	def __init__(self, default_text=''):
		super(PasteForm, self).__init__()
		self.area.default = default_text # not working rn

class UploadForm(object):
	multiple = False
	upload = FileField(
		_('Upload file'))

class SampleForm(object):
	sample = SelectField(
		_('Sample'))

	def __init__(self, tool_id):
		super(SampleForm, self).__init__()
		self.sample.choices = filehandler.get_samples(tool_id)

class MultipleSampleForm(object):
	samples = SelectMultipleField(
		_('Samples'))

	def __init__(self, tool_id):
		super(MultipleSampleForm, self).__init__()
		self.samples.choices = filehandler.get_samples(tool_id)

class LinkForm(object):
	field_flags = ('url',)
	link = StringField(
		_('Link to spreadsheet'),
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
	def __init__(self):
		super(WordCounterSample, self).__init__('wordcounter')

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
		widget=TextInput())

class SameDiffUpload(UploadForm, SameDiffForm, Form):
	multiple = True

class SameDiffSample(MultipleSampleForm, SameDiffForm, Form):
	def __init__(self):
		super(SameDiffSample, self).__init__('samediff')
