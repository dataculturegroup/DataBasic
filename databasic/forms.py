import os, json
from logic import filehandler
from werkzeug import secure_filename
from flask.ext.babel import lazy_gettext as _
from flask_wtf import Form
from flask_wtf.file import FileField
from wtforms import StringField, BooleanField, RadioField, SelectField, SelectMultipleField
from wtforms.widgets import TextArea, TextInput, CheckboxInput

class PasteForm(object):
	label = _('Paste some text')
	glyphicon = 'glyphicon-paste'
	area = StringField(
		_('Text'),
		description={'placeholder': _('Paste text...')},
		widget=TextArea()) 
	
	def __init__(self, default_text=''):
		super(PasteForm, self).__init__()
		self.area.default = default_text # not working rn

class UploadForm(object):
	label = _('Upload a file')
	glyphicon = 'glyphicon-upload'
	multiple = False
	upload = FileField(
		_('Upload file'),
		description={'placeholder': _('Upload...')})

class SampleForm(object):
	label = _('Use a sample')
	glyphicon = 'glyphicon-file'
	sample = SelectField(
		_('Sample'))

	def __init__(self, tool_id):
		super(SampleForm, self).__init__()
		self.sample.choices = filehandler.get_samples(tool_id)

class MultipleSampleForm(object):
	label = _('Use samples')
	glyphicon = 'glyphicon-file'
	samples = SelectMultipleField(
		_('Samples'))

	def __init__(self, tool_id):
		super(MultipleSampleForm, self).__init__()
		self.samples.choices = filehandler.get_samples(tool_id)

class LinkForm(object):
	label = _('Link to a spreadsheet')
	glyphicon = 'glyphicon-link'
	field_flags = ('url',)
	link = StringField(
		_('Link to spreadsheet'),
		description={'placeholder': _('https://docs.google.com/spreadsheets/')},
		widget=TextInput())

'''
Word-Counter forms
'''
class WordCounterForm(object):
	# ignore_case = BooleanField(
	# 	_('Ignore case'), 
	# 	widget=CheckboxInput(), 
	# 	default=True)
	# ignore_stopwords = BooleanField(
	# 	_('Ignore stopwords'),
	# 	widget=CheckboxInput(), 
	# 	default=True)
	pass

class WordCounterPaste(PasteForm, WordCounterForm, Form):
	ignore_case_paste = BooleanField(
		_('Ignore case'), 
		widget=CheckboxInput(), 
		default=True)
	ignore_stopwords_paste = BooleanField(
		_('Ignore stopwords'),
		widget=CheckboxInput(), 
		default=True)
	def __init__(self, default_text=''):
		super(WordCounterPaste, self).__init__(default_text)

class WordCounterUpload(UploadForm, WordCounterForm, Form):
	ignore_case_upload = BooleanField(
		_('Ignore case'), 
		widget=CheckboxInput(), 
		default=True)
	ignore_stopwords_upload = BooleanField(
		_('Ignore stopwords'),
		widget=CheckboxInput(), 
		default=True)
	pass

class WordCounterSample(SampleForm, WordCounterForm, Form):
	ignore_case_sample = BooleanField(
		_('Ignore case'), 
		widget=CheckboxInput(), 
		default=True)
	ignore_stopwords_sample = BooleanField(
		_('Ignore stopwords'),
		widget=CheckboxInput(), 
		default=True)
	def __init__(self):
		super(WordCounterSample, self).__init__('wordcounter')

'''
WTFcsv forms
'''
class WTFCSVUpload(UploadForm, Form):
	pass

class WTFCSVLink(LinkForm, Form):
	pass

class WTFCSVSample(SampleForm, Form):
	def __init__(self):
		super(WTFCSVSample, self).__init__('wtfcsv')

'''
SameDiff forms
'''
class SameDiffForm(object):
	email = StringField(
		_('Email'),
		description={'placeholder': _('kate@bush.com')},
		widget=TextInput())

class SameDiffUpload(UploadForm, SameDiffForm, Form):
	label = _('Upload files')
	multiple = True

class SameDiffSample(MultipleSampleForm, SameDiffForm, Form):
	def __init__(self):
		super(SameDiffSample, self).__init__('samediff')
