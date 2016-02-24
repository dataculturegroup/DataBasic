import os, random, logging
from collections import OrderedDict
from databasic import app, mongo, get_base_dir
from databasic.forms import WordCounterPaste, WordCounterUpload, WordCounterSample, WordCounterLink
from databasic.logic import wordhandler, filehandler, oauth
from flask import Blueprint, render_template, request, redirect, g, abort, send_from_directory
from flask.ext.babel import lazy_gettext as _

mod = Blueprint('wordcounter', __name__, url_prefix='/<lang_code>/wordcounter', template_folder='../templates/wordcounter')

logger = logging.getLogger(__name__)

@mod.route('/', methods=('GET', 'POST'))
def index():

    words = None

    forms = OrderedDict()
    forms['sample'] = WordCounterSample()
    forms['paste'] = WordCounterPaste('I am Sam\nSam I am\nThat Sam-I-am!\nThat Sam-I-am!\nI do not like that Sam-I-am!\nDo you like \ngreen eggs and ham?\nI do not like them, Sam-I-am.\nI do not like\ngreen eggs and ham.\nWould you like them \nhere or there?\nI would not like them\nhere or there.\nI would not like them anywhere.')
    forms['upload'] = WordCounterUpload()
    forms['link'] = WordCounterLink()

    if request.method == 'POST':
        ignore_case = True
        ignore_stopwords = True
        
        btn_value = request.form['btn']
        sample_id = ''

        if btn_value == 'paste':
            words = forms['paste'].data['area']
            ignore_case = forms[btn_value].data['ignore_case_paste']
            ignore_stopwords = forms[btn_value].data['ignore_stopwords_paste']
            logger.debug("New from paste: %d chars", len(words) )
            title = _('your text')
        elif btn_value == 'upload':
            upload_file = forms['upload'].data['upload']
            words = process_upload(upload_file)
            ignore_case = forms[btn_value].data['ignore_case_upload']
            ignore_stopwords = forms[btn_value].data['ignore_stopwords_upload']
            title = upload_file.filename
            logger.debug("New from upload: %s", title )
        elif btn_value == 'sample':
            sample_source = forms['sample'].data['sample']
            samplename = filehandler.get_sample_title(sample_source)
            title = samplename
            ignore_case = forms[btn_value].data['ignore_case_sample']
            ignore_stopwords = forms[btn_value].data['ignore_stopwords_sample']
            sample_id = title+str(ignore_case)+str(ignore_stopwords)
            existing_doc_id = mongo.results_for_sample('wordcounter',sample_id)
            if existing_doc_id is not None:
                logger.debug("Existing from sample: %s", sample_source)
                return redirect(request.url + 'results/' + existing_doc_id)
            logger.info("New from sample: %s", sample_source)
            sample_path = filehandler.get_sample_path(sample_source)
            logger.debug("  loading from %s", sample_path)
            words = filehandler.convert_to_txt(sample_path)
        elif btn_value == 'link':
            url = forms['link'].data['link']
            # TODO: should actually accept https
            if 'https://' in url:
                url = url.replace('https', 'http')
            elif not 'http://' in url:
                url = 'http://' + url
            logger.debug("New from link: %s", url)
            content = filehandler.download_webpage(url)
            words = content['text']
            ignore_case = forms[btn_value].data['ignore_case_link']
            ignore_stopwords = forms[btn_value].data['ignore_stopwords_link']
            title = _(content['title'])

        if words is not None:
            counts = process_words(words, ignore_case, ignore_stopwords, btn_value=='sample')
            doc_id = mongo.save_words('wordcounter', counts, ignore_case, ignore_stopwords, title, sample_id, btn_value)
            return redirect(request.url + 'results/' + doc_id + '?submit=true')

    return render_template('wordcounter.html', forms=forms.items(), tool_name='wordcounter')

@mod.route('/results/<doc_id>')
def results(doc_id):
    
    counts = None
    results = []
    remaining_days = None

    try:
        doc = mongo.find_document('wordcounter', doc_id)
        if doc['sample_id'] == u'':
            remaining_days = mongo.get_remaining_days('wordcounter', doc_id)
    except:
        logger.warning("Unable to find doc '%s'", doc_id)
        return render_template('no_results.html', tool_name='wordcounter')

    counts = doc.get('counts')

    # only render the top 40 results on the page (the csv contains all results)
    for c in range(len(counts)):
        results.append([])
        for w in range(_clamp(len(counts[c]), 0, 40)):
            results[c].append(counts[c][w])

    max_index = min(20, len(results[0]))
    min_index = max(0, max_index-5)
    random_unpopular_word = ['','']
    top_word = ''
    word_in_bigrams_count = 0
    word_in_trigrams_count = 0

    if len(results[0]) > 0:
        random_unpopular_word = results[0][random.randrange(min_index, max_index+1)] if len(results[0]) > 1 else results[0][0]

        '''
        Find the most popular word that is also present in bigrams and trigrams. 
        If none can be found, just get the most popular word.
        '''

        if len(results) == 3:
            for word in results[0]:
                top_word = word[0]
                word_in_bigrams_count = 0
                word_in_trigrams_count = 0
                for b in results[1]:
                    if top_word in b[0]:
                        word_in_bigrams_count += 1
                for t in results[2]:
                    if top_word in t[0]:
                        word_in_trigrams_count += 1
                if word_in_bigrams_count > 0 and word_in_trigrams_count > 0:
                    break   

        if word_in_bigrams_count == 0 and word_in_trigrams_count == 0:
            top_word = results[0][0][0]

    whatnext = {}
    whatnext['top_word'] = top_word
    whatnext['word_in_bigrams_count'] = word_in_bigrams_count
    whatnext['word_in_trigrams_count'] = word_in_trigrams_count
    whatnext['random_unpopular_word'] = random_unpopular_word[0]
    whatnext['random_unpopular_word_count'] = random_unpopular_word[1]

    return render_template('wordcounter/results.html', 
        results=results, 
        whatnext=whatnext, 
        tool_name='wordcounter', 
        title=doc['title'], 
        doc_id=doc_id, 
        source=doc['source'], 
        remaining_days=remaining_days)

@mod.route('/results/<doc_id>/download/<analysis_type>.csv')
def download_csv(doc_id, analysis_type):
    logger.debug("Download %s", analysis_type)
    if analysis_type not in ['words','bigrams','trigrams']:
        logger.warning("Requested unknown csv type: %s",analysis_type)
        abort(400)
    try:
        doc = mongo.find_document('wordcounter', doc_id)
    except:
        logger.warning("Unable to find doc '%s'", doc_id)
        abort(400)
    file_path = create_csv_file(doc.get('counts'),analysis_type)
    logger.debug('  created %s csv to download at %s', analysis_type, file_path)
    if file_path is None:
        abort(500)
    return filehandler.generate_csv(file_path)

@mod.route('/wordcounter-activity-guide.pdf')
def download_activity_guide():
    filename = "WordCounter Activity Guide.pdf"
    dir_path = os.path.join(get_base_dir(),'databasic','static','files','activity-guides',g.current_lang)
    logger.debug("download activity guide from %s/%s", dir_path, filename)
    return send_from_directory(directory=dir_path, filename=filename)

def process_upload(doc):
    file_path = filehandler.open_doc(doc)
    file_size = os.stat(file_path).st_size # because browser might not have sent content_length
    logger.debug("Upload: %d bytes", file_size)
    words = filehandler.convert_to_txt(file_path)
    filehandler.delete_file(file_path)
    return words

def process_words(words, ignore_case, ignore_stopwords, is_sample):
    # stopwords_language = 'english' if is_sample or g.current_lang == 'en' else 'spanish'
    stopwords_language = 'english'
    if not is_sample:
        if g.current_lang == 'es':
            stopwords_language = 'spanish'
        elif g.current_lang == 'pt':
            stopwords_language = 'portuguese'
    counts = wordhandler.get_word_counts(
        words,
        ignore_case,
        ignore_stopwords,
        stopwords_language)
    return counts

def create_csv_file(counts,analysis_type):
    if analysis_type == 'words':
        return filehandler.write_to_csv(['word', 'frequency'], counts[0], '-word-counts.csv')
    elif analysis_type == 'bigrams':
        bigrams = []
        for w in counts[1]:
            freq = w[1]
            phrase = " ".join(w[0])
            bigrams.append([phrase, freq])
        return filehandler.write_to_csv(['bigram phrase', 'frequency'], bigrams, '-bigram-counts.csv')
    elif analysis_type == 'trigrams':
        trigrams = []
        for w in counts[2]:
            freq = w[1]
            phrase = " ".join(w[0])
            trigrams.append([phrase, freq])
        return filehandler.write_to_csv(['trigram phrase', 'frequency'], trigrams, '-trigram-counts.csv')
    logger.error("Requested unknown csv type: %s",analysis_type)
    return None # if was an invalid analysis_type

def _clamp(n, minn, maxn):
    return max(min(maxn, n), minn)
