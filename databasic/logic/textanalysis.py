import textmining, logging
from scipy import spatial

def term_document_matrix(texts):
    term_doc_matrix = textmining.TermDocumentMatrix(tokenizer=textmining.simple_tokenize_remove_stopwords)
    for t in texts:
        term_doc_matrix.add_doc(t)
    return term_doc_matrix

def common_and_unique_word_freqs(texts):
    word_count_d1 = len(texts[0].split())
    word_count_d2 = len(texts[1].split())
    tdm = term_document_matrix(texts)
    # get the most common used words, sorted by freq
    common_rows = tdm.rows(cutoff=2)
    common_terms = next(common_rows)
    common_d1_freqs = next(common_rows)
    common_d2_freqs = next(common_rows)
    total_uses = [t1 + t2 for t1,t2 in zip(common_d1_freqs,common_d2_freqs)]
    common_word_freqs = list(zip(total_uses,common_terms))
    common_word_freqs.sort(reverse=True)
    # get word counts of common terms in each document
    common_counts = [list(zip(common_d1_freqs, common_terms)), list(zip(common_d2_freqs, common_terms))]
    common_counts[0].sort(reverse=True)
    common_counts[1].sort(reverse=True)
    # get all the rows for unique-to-doc calculations
    all_rows = tdm.rows(cutoff=0)
    all_terms = next(all_rows)
    all_d1_freqs = next(all_rows)
    all_d2_freqs = next(all_rows)
    # get the doc1 words
    d1 = [ (f1,t) for t,f1 in zip(all_terms,all_d1_freqs) if f1>0]
    d1.sort(reverse=True)
    # get the doc2 words
    d2 = [ (f2,t) for t,f2 in zip(all_terms,all_d2_freqs) if f2>0]
    d2.sort(reverse=True)
    # get the unique doc1 words
    unique_to_d1 = [ (f1,t) for t,f1,f2 in zip(all_terms,all_d1_freqs,all_d2_freqs) if f2 == 0]
    unique_to_d1.sort(reverse=True)
    # get the unique doc2 words
    unique_to_d2 = [ (f2,t) for t,f1,f2 in zip(all_terms,all_d1_freqs,all_d2_freqs) if f1 == 0]
    unique_to_d2.sort(reverse=True)
    # compute cosine similarity too
    cosine_similarity = ( 1 - spatial.distance.cosine(all_d1_freqs,all_d2_freqs) )

    # stitch it together to return the data
    return {'common': common_word_freqs, 'common_counts': common_counts, 'doc1': d1, 'doc2':d2, 
            'doc1unique': unique_to_d1, 'doc2unique': unique_to_d2,
            'doc1total': word_count_d1, 'doc2total': word_count_d2,
            'cosine_similarity': cosine_similarity}