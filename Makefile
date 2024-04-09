.DEFAULT_GOAL := all

# global named targets
all: cyr lat
cyr: cyr.num.generator.hfst cyr.num.analyzer.hfst
lat: lat.num.generator.hfst lat.num.analyzer.hfst
clear:
	rm *.hfst
	rm translit/*.hfst

# transliterators
translit/cyr2lat.hfst: translit/lat2cyr.hfst
	hfst-invert $< -o $@
translit/lat2cyr.hfst: translit/correspondence.hfst
	hfst-repeat -f 1 $< -o $@
translit/correspondence.hfst: translit/lat2cyr_correspondence
	hfst-strings2fst -j $< -o $@
translit/fixes.hfst: translit/lat2cyr_fixes
	hfst-strings2fst -j $< -o $@

# anylizer and generator
## cyr
cyr.num.generator.hfst: num.lexd
	lexd $< | hfst-txt2fst -o $@
cyr.num.analyzer.hfst: cyr.num.generator.hfst
	hfst-invert $< -o $@
## lat
lat.num.generator.hfst: cyr.num.generator.hfst translit/cyr2lat.hfst
	hfst-compose $^ -o $@
lat.num.analyzer.hfst: lat.num.generator.hfst
	hfst-invert $< -o $@

# create and run tests
#test.pass.txt: tests.csv
#	awk -F, '$$3 == "pass" {print $$1 ":" $$2}' $^ | sort -u > $@
#check: and.noun.generator.hfst test.pass.txt
#	bash compare.sh $^
#clean: check
#	rm test.*