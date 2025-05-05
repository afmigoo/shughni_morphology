.DEFAULT_GOAL := analyze_stem_word_cyr.hfst
SHELL=/bin/bash -o pipefail

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
	rm -f translit/*.hfst translit/*.hfstol
	rm -f translate/*.hfst translate/*.hfstol translate/*.lexd
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
	hfst-compose-intersect $^ -o $@
## cyrillic transducers with no morpheme borders
# wискӯн<n>><loc>:wискӯнанд or wискӯн<n>><loc>:wискӯн-анд
sgh_gen_stem_word_cyr.hfst: sgh_base_stem.hfst twol/sep.hfst
	hfst-compose-intersect $^ -o $@

## Russian lemmas instead of shughni stems
# вилы<n>><loc>:wискӯн>-анд
sgh_base_rulem.hfst: translate/rulem2sgh.hfst sgh_base_stem.hfst
	hfst-compose $^ -o $@
# вилы<n>><loc>:wискӯн>анд
sgh_gen_rulem_morph_cyr.hfst: sgh_base_rulem.hfst twol/bar.hfst
	hfst-compose-intersect $^ -o $@
# вилы<n>><loc>:wискӯнанд or вилы<n>><loc>:wискӯн-анд
sgh_gen_rulem_word_cyr.hfst: sgh_base_rulem.hfst twol/sep.hfst
	hfst-compose-intersect $^ -o $@

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
RESULTS_DIR := $(ACCURACY_DIR)/results
EAF_FILES := $(wildcard $(ACCURACY_DIR)/elans/*.eaf)
CSV_FILES := $(patsubst $(ACCURACY_DIR)/elans/%.eaf,$(ACCURACY_DIR)/csv/%.csv,$(EAF_FILES))
DETAIL_DIRS := $(patsubst $(ACCURACY_DIR)/elans/%.eaf,$(RESULTS_DIR)/%,$(EAF_FILES))

accuracy: accuracy_data
	cat $(ACCURACY_DIR)/csv/*.csv | grep -v "wordform,tagged" | $(ACCURACY_DIR)/eval.py -p \
		--hfst-analyzer sgh_analyze_stem_word_lat.hfstol \
		--hfst-translit translit/cyr2lat.hfstol \
		--details-dir $(ACCURACY_DIR)/results/total
accuracy_individual_files: $(DETAIL_DIRS)
$(ACCURACY_DIR)/results/%: $(ACCURACY_DIR)/csv/%.csv
	cat $< | grep -v "wordform,tagged" | $(ACCURACY_DIR)/eval.py -p \
		--hfst-analyzer sgh_analyze_stem_word_lat.hfstol \
		--hfst-translit translit/cyr2lat.hfstol \
		--details-dir $@

accuracy_results_clear:
	rm -r $(RESULTS_DIR)

accuracy_data: $(CSV_FILES)
accuracy_data_clear: 
	rm $(ACCURACY_DIR)/csv/*.csv
$(ACCURACY_DIR)/csv/%.csv: $(ACCURACY_DIR)/elans/%.eaf
	$(ACCURACY_DIR)/elan2csv.py $< $@

# Coverage
COVERAGE_DIR := scripts/coverage
coverage:
	cat $(COVERAGE_DIR)/corpus/* | $(COVERAGE_DIR)/eval.py

