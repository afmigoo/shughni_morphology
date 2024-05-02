.DEFAULT_GOAL := get-coverage

get-coverage: corpus/shugni-test-fit.txt
	cat $< | python3 calc.py

corpus/shugni-test-fit.txt:
	python3 process_corpus.py
