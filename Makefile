.DEFAULT_GOAL := cyr

# global named targets
all: clear cyr lat
cyr: shughni.gen.hfst shughni.analyze.hfst
lat: shughni.gen.latin.hfst shughni.analyze.latin.hfst
clear: clear_tests
	rm -f *.hfst
	rm -f translit/*.hfst
	rm -f twol/*.hfst
	rm -f shughni.lexd

# anylizers and generators
## cyr
shughni.gen.hfst: shughni.lexd twol/all.twol.hfst
	lexd $< | hfst-txt2fst | hfst-compose-intersect twol/all.twol.hfst -o $@
shughni.analyze.hfst: shughni.gen.hfst
	hfst-invert $< -o $@
## lat
shughni.gen.latin.hfst: shughni.gen.hfst translit/cyr2lat.hfst
	hfst-compose $^ -o $@
shughni.analyze.latin.hfst: shughni.gen.latin.hfst
	hfst-invert $< -o $@

# twol
twol/%.twol.hfst: twol/%.twol
	hfst-twolc $< -o $@
# final lexd
shughni.lexd:
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
check.%: shughni.gen.hfst test.%.txt
	bash compare.sh $^
test.%.txt: tests/%.csv
	awk -F, '$$3 == "pass" {print $$1 ":" $$2}' $^ | sort -u > $@