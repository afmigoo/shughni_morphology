.DEFAULT_GOAL := cyr

########################
# global named targets #
########################
all: clear cyr_all lat_all
cyr_all: cyr_morph cyr_word
lat_all: lat_morph lat_word

cyr_morph: sgh_gen_morph_cyr.hfst sgh_analyze_morph_cyr.hfst
lat_morph: sgh_gen_morph_lat.hfst sgh_analyze_morph_lat.hfst
cyr_word: sgh_gen_word_cyr.hfst sgh_analyze_word_cyr.hfst
lat_word: sgh_gen_word_lat.hfst sgh_analyze_word_lat.hfst

clear: clear_tests
	rm -f *.hfst
	rm -f translit/*.hfst
	rm -f twol/*.hfst
	rm -f sgh.lexd

############################
# analyzers and generators #
############################
# generator with unfiltered mixed morpheme borders
# wискӯн<n>><loc>:wискӯн>-анд
sgh_gen.hfst: sgh.lexd twol/all.hfst
	lexd $< | hfst-txt2fst | hfst-compose-intersect twol/all.hfst -o $@
# cyrillic morph-separated transducers
# wискӯн<n>><loc>:wискӯн>анд
sgh_gen_morph_cyr.hfst: sgh_gen.hfst twol/bar.hfst
	hfst-compose-intersect $^ | hfst-minimize -o $@
# cyrillic transducers with no morpheme borders
# wискӯн<n>><loc>:wискӯнанд or wискӯн<n>><loc>:wискӯн-анд
sgh_gen_word_cyr.hfst: sgh_gen.hfst twol/sep.hfst
	hfst-compose-intersect $^ | hfst-minimize -o $@
# latin versions of transducers
# wискӯн<n>><loc>:wiskūn>and
# wискӯн<n>><loc>:wiskūnand or wискӯн<n>><loc>:wiskūn-and
sgh_gen_%_lat.hfst: sgh_gen_%_cyr.hfst translit/cyr2lat.hfst
	hfst-compose $^ -o $@
# every analyzer is just an inverted generator
sgh_analyze_%.hfst: sgh_gen_%.hfst
	hfst-invert $< -o $@

############################
# analyzers and generators #
############################
# twol
twol/%.hfst: twol/%.twol
	hfst-twolc $< -o $@
# final lexd
sgh.lexd: lexd/lexicons/*.lexd lexd/*.lexd
	cat lexd/lexicons/*.lexd lexd/*.lexd > $@

# transliterators
translit/cyr2lat.hfst: translit/lat2cyr.hfst
	hfst-invert $< -o $@
translit/lat2cyr.hfst: translit/lat2cyr_correspondence
	hfst-strings2fst -j $< | hfst-repeat -o $@

# create and run tests
test: check.num check.noun check.verb
clear_tests:
	rm -f test.*
check.%: sgh_gen_morph_cyr.hfst test.%.txt
	bash compare.sh $^
test.%.txt: tests/%.csv
	awk -F, '$$3 == "pass" {print $$1 ":" $$2}' $^ | sort -u > $@