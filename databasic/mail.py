import logging
from flask_mail import Message

from databasic import app, mail

logger = logging.getLogger(__name__)

DEFAULT_SENDER = app.config.get('MAIL_USERNAME')


def send_email(sender, recipients, subject, message):
    logger.debug('Sending mail '+sender+':'+subject)
    msg = Message(subject,
                  sender=sender,
                  recipients=recipients)
    msg.body = message
    mail.send(msg)

'''
def send_html_email(subject, recipients, text_body, html_body):
    msg = Message(subject, sender=DEFAULT_SENDER, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)
'''
