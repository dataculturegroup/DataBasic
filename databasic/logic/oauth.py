import gspread, logging
from google_auth_oauthlib.flow import Flow
import google.auth.transport.requests

_oauth = None   # singleton instance

logger = logging.getLogger(__name__)

'''
Public API
'''
def init(client_id,client_secret,redirect_uri):
    global _oauth
    logger.info("Init oauth with redirect to %s", redirect_uri)
    if len(client_id)>0 and len(client_secret)>0:
        logging.info("Initialized oauth with id & secret")
        _oauth = OAuthHandler(client_id,client_secret,redirect_uri)
    else: 
        logging.error("No client_id and client_secret specificed - oauth won't work!")

def authorize(code):
    logger.debug("authorize %s", code)
    _oauth.authorize(code)

def redirect_to():
    return _oauth.redirect_to

def doc_url():
    return _oauth.get_doc_url()

'''
Handler for Google's OAuth2
https://gist.github.com/cspickert/1650271
'''
class OAuthHandler:

    def __init__(self, client_id, client_secret, redirect_uri):
        self.authorized = False
        self.redirect_to = '' # the url to return to after the user has granted permissions
        self.doc_url = None   # the url of the doc to open after the user has granted permissions
        self._key = { 'client_id': client_id, 'client_secret': client_secret}
        self._client = None     # initialize so we can check later

        self.scopes = [
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/spreadsheets.readonly",
        ]

        client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }
        }

        self.flow = Flow.from_client_config(
            client_config,
            scopes=self.scopes,
            redirect_uri=redirect_uri,
        )

    def authenticate_app(self):
        logger.debug("OAuthHandler.authenticate_app")
        auth_url, state = self.flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",   # ensures refresh token on first consent
        )
        self._state = state
        return auth_url

    def authorize(self, code):
        logger.debug("OAuthHandler.authorize")
        self.flow.fetch_token(code=code)
        creds = self.flow.credentials
        request = google.auth.transport.requests.Request()
        if creds.expired and creds.refresh_token:
            creds.refresh(request)
        self._client = gspread.authorize(creds)
        self.authorized = True

    def open_url(self, url):
        # TODO: make this work with docs as well (only spreadsheets work at the moment)
        # ^^ (this is very hard :o) ^^
        if self._client is None:
            logger.debug("OAuthHandler doesn't have _client yet")
            return None
        try:
            logger.debug("OAuthHandler.open_url")
            return self._client.open_by_url(url)
        except gspread.SpreadsheetNotFound:
            logger.error("open_url: spreadsheet not found %s", url)
            self.authorized = False
            return None
        except gspread.NoValidUrlKeyFound:
            logger.error("open_url: no valid url found %s", url)
            self.authorized = False
            return None

    def get_doc_url(self):
        logger.debug("get_doc_url")
        if self.doc_url is None:
            return None
        u = self.open_url(self.doc_url)
        self.doc_url = None
        return u
