from werkzeug import secure_filename
from flask_wtf import Form
from flask_wtf.file import FileField
from wtforms import StringField, BooleanField
from wtforms.fields import RadioField
from wtforms.widgets import TextArea, TextInput, CheckboxInput
from wtforms.validators import Length, Regexp, Optional, Required, URL

class PULForm(object):
	'''
	Paste/Upload/Link form
	'''
	input_type = RadioField(
		u'Choose input type',
		choices=[(u'paste', u'Paste'), (u'upload', u'Upload'), (u'link', u'Link')])

class WordCountForm(PULForm, Form):
	area = StringField(
		u'Text',
		validators=[Required(), Length(min=1)], 
		widget=TextArea(), 
		default='I am Sam\nSam I am\nThat Sam-I-am!\nThat Sam-I-am!\nI do not like that Sam-I-am!\nDo you like \ngreen eggs and ham?\nI do not like them, Sam-I-am.\nI do not like\ngreen eggs and ham.\nWould you like them \nhere or there?\nI would not like them\nhere or there.\nI would not like them anywhere.')
	upload = FileField(
		u'Upload file',
		# validators=[Regexp(u'^.*\.(txt|docx)$')])
		validators=[Required()])
	link = StringField(
		u'Link to doc',
		validators=[Required(), URL()],
		widget=TextInput())
	ignore_case = BooleanField(
		u'Ignore case', 
		widget=CheckboxInput(), 
		default=True)
	ignore_stopwords = BooleanField(
		u'Ignore stopwords',
		widget=CheckboxInput(), 
		default=True)
	def validate(self):
		input_type = self.input_type.data
		if input_type == 'paste':
			return self.area.validate(self)
		elif input_type == 'upload':
			return self.upload.validate(self)
		elif input_type == 'link':
			return self.link.validate(self)
		return Form.validate(self)

class WTFCSVForm(PULForm, Form):
	area = StringField(
		u'Paste CSV',
		validators=[Length(min=1)],
		widget=TextArea(),
		default='name, shirt_color, siblings\nRahul, blue, 1\nCatherine, red, 2')
	upload = FileField(
		u'Upload file')#,
		# validators=[Regexp(u'^.*\.(csv)$')]) not sure why this validation isn't working
	link = StringField(
		u'Link to spreadsheet',
		validators=[URL()],
		widget=TextInput())
	def validate(self):
		input_type = self.input_type.data
		if input_type == 'paste':
			return self.area.validate(self)
		elif input_type == 'upload':
			return self.upload.data.filename.endswith('.csv')
		elif input_type == 'link':
			return self.link.validate(self)
		return Form.validate(self)
