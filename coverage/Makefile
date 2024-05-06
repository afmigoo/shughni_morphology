.DEFAULT_GOAL := get-coverage

get-coverage: corpus
	cat $</* | python3 calc.py

corpus/shugni-test-fit.txt:
	python3 process_corpus.py
