.DEFAULT_GOAL := cyr

# global named targets
all: clear cyr lat
cyr: shugni.gen.hfst shugni.anal.hfst
lat: shugni.gen.latin.hfst shugni.anal.latin.hfst
clear: clear_tests
	rm -f *.hfst
	rm -f translit/*.hfst
	rm -f twol/*.hfst
	rm -f shugni.lexd

# anylizers and generators
## cyr
shugni.gen.hfst: shugni.lexd twol/all.twol.hfst
	lexd $< | hfst-txt2fst | hfst-compose-intersect twol/all.twol.hfst -o $@
shugni.anal.hfst: shugni.gen.hfst
	hfst-invert $< -o $@
## lat
shugni.gen.latin.hfst: shugni.gen.hfst translit/cyr2lat.hfst
	hfst-compose $^ -o $@
shugni.anal.latin.hfst: shugni.gen.latin.hfst
	hfst-invert $< -o $@

# twol
twol/all.twol.hfst: twol/all.twol
	hfst-twolc $< -o $@
# final lexd
shugni.lexd:
	cat lexd/lexicons/*.lexd lexd/*.lexd > $@

# transliterators
translit/cyr2lat.hfst: translit/lat2cyr.hfst
	hfst-invert $< -o $@
translit/lat2cyr.hfst: translit/lat2cyr_correspondence
	hfst-strings2fst -j $< | hfst-repeat -o $@

# create and run tests
test: check.num check.noun
clear_tests:
	rm -f test.*
check.%: shugni.gen.hfst test.%.txt
	bash compare.sh $^
test.%.txt: tests/%.csv
	awk -F, '$$3 == "pass" {print $$1 ":" $$2}' $^ | sort -u > $@