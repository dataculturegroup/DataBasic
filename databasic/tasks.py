from __future__ import absolute_import
import mongo, os
from databasic.celery import celery_app
from envelopes import Envelope

@celery_app.task(serializer='json',bind=True)
def save_tfidf_results(self,job_id):
    job_info = mongo.find_job(job_id)
    # tfidf them
    filepaths = job_info['filepaths']
    tfidf = samediff.analysis.tf_idf(filepaths)
    cosine_similarity = samediff.analysis.cosine_similarity(filepaths)
    # save the results back to the db (based on the job_number)
    job_info['tfidf'] = tfidf
    job_info['cosineSimilarity'] = cosine_similarity
    # delete the raw input files
    for path in job_info['filepaths']:
        os.remove(path)
    del job_info['filepaths']
    job_info['status'] = 'complete'
    mongo.save_job(job_info)
    # TODO: catch any exceptions and queue them up for retry attempts
    
    # notify them with email
    # TODO: Internationalize and put the text stuff into some kind of templating structure
    name = job_info['email'].split('@')[0]
    body = u'Dear %s, \n\nYour SameDiff job is ready at this URL: %s! \n\nSincerely, \n %s ' % ( name , job_info["results_url"], app.config["EMAIL_FROM_NAME"])
    envelope = Envelope(
        from_addr=(app.config["EMAIL_FROM_EMAIL"], app.config["EMAIL_FROM_NAME"]),
        to_addr=(job_info['email'], name),
        subject=u'Your SameDiff job is ready!',
        text_body=body)
    envelope.send('mail.gandi.net', login=app.config["EMAIL_LOGIN"],
              password=app.config["EMAIL_PASSWORD"], tls=True)