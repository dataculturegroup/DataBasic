import os, sys, json, gspread, logging
import gdata.docs.service
from oauth2client.client import SignedJwtAssertionCredentials, OAuth2WebServerFlow


_oauth = None   # singleton instance

'''
Public API
'''
def init(client_id,client_secret):
    global _oauth
    if len(client_id)>0 and len(client_secret)>0:
        logging.info("Initialized oauth with id & secret")
        _oauth = OAuthHandler(client_id,client_secret)
    else: 
        logging.error("No client_id and client_secret specificed - oauth won't work!")

def authorize(code):
    _oauth.authorize(code)

def open_doc_from_url(url, redirect_to):
    _oauth.redirect_to = redirect_to
    if not _oauth.authorized:
        _oauth.doc_url = url
        return {
            'authenticate': _oauth.authenticate_app(),
            'doc': None
        }
    else:
        _oauth.doc_url = None
        return {
            'authenticate': None,
            'doc': _oauth.open_url(url)
        }

def redirect_to():
    return _oauth.redirect_to

def doc_url():
    return _oauth.get_doc_url()

'''
Handler for Google's OAuth2
https://gist.github.com/cspickert/1650271
'''
class OAuthHandler:

    def __init__(self, client_id, client_secret, redirect_uri='http://localhost:5000/auth'):
        self.authorized = False
        self.redirect_to = '' # the url to return to after the user has granted permissions
        self.doc_url = None   # the url of the doc to open after the user has granted permissions
        self._data_client = gdata.docs.service.DocsService() # used for docs
        self._key = { 'client_id': client_id, 'client_secret': client_secret}
        self.flow = OAuth2WebServerFlow(
            client_id=self._key['client_id'],
            client_secret=self._key['client_secret'],
            scope=[
                'https://www.googleapis.com/auth/drive.readonly', 
                'https://spreadsheets.google.com/feeds', 
                'https://docs.google.com/feeds'],
            redirect_uri=redirect_uri)

    def authenticate_app(self):
        return self.flow.step1_get_authorize_url()

    def authorize(self, code):
        credentials = self.flow.step2_exchange(code)
        self._client = gspread.authorize(credentials)
        self._data_client.ClientLogin(self._key['client_id'], self._key['client_secret'])
        self.authorized = True

    def open_url(self, url):
        # TODO: make this work with docs as well (only spreadsheets work at the moment)
        # ^^ (this is very hard :o) ^^
        try:
            return self._client.open_by_url(url)
        except gspread.SpreadsheetNotFound:
            self.authorized = False
            return None
        except gspread.NoValidUrlKeyFound:
            self.authorized = False
            return None

    def get_doc_url(self):
        if self.doc_url is None:
            return None
        u = self.open_url(self.doc_url)
        self.doc_url = None
        return u
