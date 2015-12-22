from setuptools import setup,find_packages

setup(
    name='DataBasic',
    version='0.8',
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    sass_manifests={
        'databasic': ('static/sass', 'static/css')
    },
    install_requires=['flask','flask_debugtoolbar','flask-uploads','Flask-WTF',
        'Flask-Babel','Flask-Mail','pojson','requests','nltk','docx','unicodecsv',
        'csvkit','xlrd','gspread','gdata','oauth2client','pymongo','celery','redis',
        'pyth','libsass >= 0.6.0','textmining','scipy','numpy','wtforms','kombu','billiard',
        'beautifulsoup4']
)