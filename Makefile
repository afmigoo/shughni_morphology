.DEFAULT_GOAL := cyr

ALL_HFST := gen_stem_morph_cyr.hfst gen_stem_word_cyr.hfst
ALL_HFST += gen_rulem_morph_cyr.hfst gen_rulem_word_cyr.hfst
ALL_HFST += analyze_stem_morph_cyr.hfst analyze_stem_word_cyr.hfst
ALL_HFST += analyze_rulem_morph_cyr.hfst analyze_rulem_word_cyr.hfst
ALL_HFST += gen_stem_morph_lat.hfst gen_stem_word_lat.hfst
ALL_HFST += gen_rulem_morph_lat.hfst gen_rulem_word_lat.hfst
ALL_HFST += analyze_stem_morph_lat.hfst analyze_stem_word_lat.hfst
ALL_HFST += analyze_rulem_morph_lat.hfst analyze_rulem_word_lat.hfst

########################
# global named targets #
########################
all: clear $(ALL_HFST)
cyr_all: cyr_morph cyr_word
lat_all: lat_morph lat_word

clear: clear_tests
	rm -f *.hfst
	rm -f translit/*.hfst
	rm -f translate/*.hfst translate/*.lexd
	rm -f twol/*.hfst
	rm -f sgh.lexd

##############
# morphology #
##############
## generator with unfiltered mixed morpheme borders
# wискӯн<n>><loc>:wискӯн>-анд
base_stem.hfst: sgh.lexd twol/all.hfst
	lexd $< | hfst-txt2fst | hfst-compose-intersect twol/all.hfst -o $@
## cyrillic morph-separated transducers
# wискӯн<n>><loc>:wискӯн>анд
gen_stem_morph_cyr.hfst: base_stem.hfst twol/bar.hfst
	hfst-compose-intersect $^ | hfst-minimize -o $@
## cyrillic transducers with no morpheme borders
# wискӯн<n>><loc>:wискӯнанд or wискӯн<n>><loc>:wискӯн-анд
gen_stem_word_cyr.hfst: base_stem.hfst twol/sep.hfst
	hfst-compose-intersect $^ | hfst-minimize -o $@

## Russian lemmas instead of shughni stems
# вилы<n>><loc>:wискӯн>-анд
base_rulem.hfst: translate/rulem2sgh.hfst base_stem.hfst
	hfst-compose $^ -o $@
# вилы<n>><loc>:wискӯн>анд
gen_rulem_morph_cyr.hfst: base_rulem.hfst twol/bar.hfst
	hfst-compose-intersect $^ | hfst-minimize -o $@
# вилы<n>><loc>:wискӯнанд or вилы<n>><loc>:wискӯн-анд
gen_rulem_word_cyr.hfst: base_rulem.hfst twol/sep.hfst
	hfst-compose-intersect $^ | hfst-minimize -o $@

## Latin versions of transducers
# any cyr generator + cyr2lat -> lat generator
# wискӯн<n>><loc>:wiskūn>and
# вилы<n>><loc>:wiskūnand
gen_%_lat.hfst: gen_%_cyr.hfst translit/cyr2lat.hfst
	hfst-compose $^ -o $@
## Every analyzer is just an inverted generator
analyze_%.hfst: gen_%.hfst
	hfst-invert $< -o $@

########
# TWOL #
########
twol/%.hfst: twol/%.twol
	hfst-twolc $< -o $@

##############
# Final LEXD #
##############
sgh.lexd: lexd/lexicons/*.lexd lexd/*.lexd
	cat lexd/lexicons/*.lexd lexd/*.lexd > $@

#############################
# Stem to rulemma converter #
#############################
translate/sgh_rulem.lexd: translate/lexd/*.lexd
	cat $^ > $@
translate/sgh2rulem.hfst: translate/sgh_rulem.lexd
	lexd $< | hfst-txt2fst -o $@
translate/rulem2sgh.hfst: translate/sgh2rulem.hfst
	hfst-invert $< -o $@

###################
# Transliteration #
###################
translit/cyr2lat.hfst: translit/lat2cyr.hfst
	mkdir -p translit
	hfst-invert $< -o $@
translit/lat2cyr.hfst: translit/lat2cyr_correspondence
	mkdir -p translit
	hfst-strings2fst -j $< | hfst-repeat -o $@

# create and run tests
test: check.num check.noun check.verb
clear_tests:
	rm -f test.*
check.%: sgh_gen_morph_cyr.hfst test.%.txt
	bash compare.sh $^
test.%.txt: tests/%.csv
	awk -F, '$$3 == "pass" {print $$1 ":" $$2}' $^ | sort -u > $@