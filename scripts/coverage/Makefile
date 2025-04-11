.DEFAULT_GOAL := get-coverage

get-coverage:
	python3 preproc_eaf_corpus.py
	python3 preproc_txt_corpus.py
	cat corpus/* | python3 calc.py
