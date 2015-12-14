from __future__ import absolute_import
import os
from databasic import app, mongo
#from databasic import mail
#from databasic.celeryapp import celery_app
from flask.ext.mail import Message
from databasic.logic import tfidfanalysis
'''
@celery_app.task(serializer='json',bind=True)
def save_tfidf_results(self, job_id):

    job_info = mongo.find_document('samediff', job_id)

    # tfidf them
    filepaths = job_info['filepaths']
    tfidf = tfidfanalysis.tf_idf(filepaths)
    cosine_similarity = tfidfanalysis.cosine_similarity(filepaths)

    # save the results back to the db (based on the job_number)
    job_info['tfidf'] = tfidf
    job_info['cosineSimilarity'] = cosine_similarity

    # delete the raw input files
    if not job_info['is_sample_data']:
        with app.app_context():
            for path in job_info['filepaths']:
                os.remove(path)
        del job_info['filepaths']
    
    job_info['status'] = 'complete'
    mongo.save_job('samediff', job_info)
    # TODO: catch any exceptions and queue them up for retry attempts
    
    # notify them with email
    # TODO: Internationalize and put the text stuff into some kind of templating structure
    name = job_info['email'].split('@')[0]
    email_body = u'Dear %s, \n\nYour SameDiff job is ready at this URL: %s! \n\nSincerely, \n %s ' % (name, job_info['results_url'], settings.get('mail', 'from_email'))
    msg = Message(u'Your SameDiff job is ready!',
        recipients=[job_info['email']],
        body=email_body,
        sender=settings.get('mail', 'from_email'))
    with app.app_context():
        mail.send(msg)

    print "sent ya an email ;)"
'''