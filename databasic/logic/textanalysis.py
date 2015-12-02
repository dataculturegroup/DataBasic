import textmining, logging

def term_document_matrix(texts):
    term_doc_matrix = textmining.TermDocumentMatrix(tokenizer=textmining.simple_tokenize_remove_stopwords)
    for t in texts:
        term_doc_matrix.add_doc(t)
    return term_doc_matrix

def common_and_unique_word_freqs(texts):
	tdm = term_document_matrix(texts)
	# get the most common used words, sorted by freq
	common_rows = tdm.rows(cutoff=2)
	common_terms = next(common_rows)
	common_d1_freqs = next(common_rows)
	common_d2_freqs = next(common_rows)
	total_uses = [t1 + t2 for t1,t2 in zip(common_d1_freqs,common_d2_freqs)]
	common_word_freqs = zip(total_uses,common_terms)
	common_word_freqs.sort(reverse=True)
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
	unique_to_d1 = [ (f1,t) for t,f1,f2 in zip(all_terms,all_d1_freqs,all_d2_freqs) if f2 is 0]
	unique_to_d1.sort(reverse=True)
	# get the unique doc2 words
	unique_to_d2 = [ (f2,t) for t,f1,f2 in zip(all_terms,all_d1_freqs,all_d2_freqs) if f1 is 0]
	unique_to_d2.sort(reverse=True)
	# stitch it together to return the data
	return {'common':common_word_freqs, 'doc1': d1, 'doc2':d2, 
			'doc1unique':unique_to_d1, 'doc2unique': unique_to_d2}