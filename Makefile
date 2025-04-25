.DEFAULT_GOAL := analyze_stem_word_cyr.hfst

ALL_HFST := sgh_gen_stem_morph_cyr.hfst sgh_gen_stem_word_cyr.hfst
ALL_HFST += sgh_gen_rulem_morph_cyr.hfst sgh_gen_rulem_word_cyr.hfst
ALL_HFST += sgh_analyze_stem_morph_cyr.hfst sgh_analyze_stem_word_cyr.hfst
ALL_HFST += sgh_analyze_rulem_morph_cyr.hfst sgh_analyze_rulem_word_cyr.hfst
ALL_HFST += sgh_gen_stem_morph_lat.hfst sgh_gen_stem_word_lat.hfst
ALL_HFST += sgh_gen_rulem_morph_lat.hfst sgh_gen_rulem_word_lat.hfst
ALL_HFST += sgh_analyze_stem_morph_lat.hfst sgh_analyze_stem_word_lat.hfst
ALL_HFST += sgh_analyze_rulem_morph_lat.hfst sgh_analyze_rulem_word_lat.hfst

ALL_HFSTOL := $(patsubst %.hfst,%.hfstol,$(ALL_HFST))

TRANSLIT_OPTIMIZED := translit/cyr2lat.hfstol translit/lat2cyr.hfstol

################
# Main targets #
################
all: all_hfst all_hfstol test
all_hfst: $(ALL_HFST)
	rm -f sgh_base_rulem.hfst sgh_base_stem.hfst sgh_rulemma.lexd
all_hfstol: all_hfst $(ALL_HFSTOL) $(TRANSLIT_OPTIMIZED)
clean:
	rm -f *.hfst *.hfstol
	rm -f translit/*.hfst
	rm -f translate/*.hfst translate/*.lexd
	rm -f twol/*.hfst
	rm -f sgh.lexd

##############
# morphology #
##############
## generator with unfiltered mixed morpheme borders
# wискӯн<n>><loc>:wискӯн>-анд
sgh_base_stem.hfst: sgh.lexd twol/all.hfst
	lexd $< | hfst-txt2fst | hfst-compose-intersect twol/all.hfst -o $@
## cyrillic morph-separated transducers
# wискӯн<n>><loc>:wискӯн>анд
sgh_gen_stem_morph_cyr.hfst: sgh_base_stem.hfst twol/bar.hfst
	hfst-compose-intersect $^ | hfst-minimize -o $@
## cyrillic transducers with no morpheme borders
# wискӯн<n>><loc>:wискӯнанд or wискӯн<n>><loc>:wискӯн-анд
sgh_gen_stem_word_cyr.hfst: sgh_base_stem.hfst twol/sep.hfst
	hfst-compose-intersect $^ | hfst-minimize -o $@

## Russian lemmas instead of shughni stems
# вилы<n>><loc>:wискӯн>-анд
sgh_base_rulem.hfst: translate/rulem2sgh.hfst sgh_base_stem.hfst
	hfst-compose $^ -o $@
# вилы<n>><loc>:wискӯн>анд
sgh_gen_rulem_morph_cyr.hfst: sgh_base_rulem.hfst twol/bar.hfst
	hfst-compose-intersect $^ | hfst-minimize -o $@
# вилы<n>><loc>:wискӯнанд or вилы<n>><loc>:wискӯн-анд
sgh_gen_rulem_word_cyr.hfst: sgh_base_rulem.hfst twol/sep.hfst
	hfst-compose-intersect $^ | hfst-minimize -o $@

## Latin versions of transducers
# any cyr generator + cyr2lat -> lat generator
# wискӯн<n>><loc>:wiskūn>and
# вилы<n>><loc>:wiskūnand
sgh_gen_%_lat.hfst: sgh_gen_%_cyr.hfst translit/cyr2lat.hfst
	hfst-compose $^ -o $@
## Every analyzer is just an inverted generator
sgh_analyze_%.hfst: sgh_gen_%.hfst
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
translit/cyr2lat_unstressed.hfst: translit/remove_stresses.hfst translit/cyr2lat.hfst
	hfst-compose $^ -o $@
translit/lat2cyr_unstressed.hfst: translit/remove_stresses.hfst translit/lat2cyr.hfst
	hfst-compose $^ -o $@
translit/cyr2lat.hfst: translit/lat2cyr.hfst
	hfst-invert $< -o $@
translit/lat2cyr.hfst: translit/lat2cyr.lexd
	lexd $< | hfst-txt2fst -o $@
translit/remove_stresses.hfst: translit/remove_stresses.lexd
	lexd $< | hfst-txt2fst -o $@

####################
# Optimized format #
####################
%.hfstol: %.hfst
	hfst-fst2fst --optimized-lookup-unweighted $< -o $@

###########
# Testing #
###########
test: 
	python3 scripts/testing/runtests.py --multiply-cases

###########
# Metrics #
###########
metrics: coverage accuracy

# Accuracy
ACCURACY_DIR := scripts/accuracy
EAF_FILES := $(wildcard $(ACCURACY_DIR)/elans/*.eaf)
CSV_FILES := $(patsubst $(ACCURACY_DIR)/elans/%.eaf,scripts/accuracy/csv/%.csv,$(EAF_FILES))

accuracy: accuracy_data
	$(ACCURACY_DIR)/eval.py --pretty-output
accuracy_data: $(CSV_FILES)
accuracy_data_clear: 
	rm $(ACCURACY_DIR)/csv/*.csv
$(ACCURACY_DIR)/csv/%.csv: $(ACCURACY_DIR)/elans/%.eaf
	$(ACCURACY_DIR)/elan2csv.py $< $@

# Coverage
COVERAGE_DIR := scripts/coverage
coverage:
	cat $(COVERAGE_DIR)/corpus/* | $(COVERAGE_DIR)/eval.py

