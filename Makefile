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
	hfst-compose $^ | hfst-minimize -o $@
## Every analyzer is just an inverted generator
sgh_analyze_%.hfst: sgh_gen_%.hfst
	hfst-invert $< | hfst-minimize -o $@

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
metrics: metrics_quantity metrics_quality

# metrics (Recall Precision F-Score Accuracy(any))
METRICS_DIR := scripts/metrics
RESULTS_DIR := $(METRICS_DIR)/results
EAF_FILES := $(wildcard $(METRICS_DIR)/elans/*.eaf)
CSV_FILES := $(patsubst $(METRICS_DIR)/elans/%.eaf,$(METRICS_DIR)/csv/%.csv,$(EAF_FILES))
DETAIL_DIRS := $(patsubst $(METRICS_DIR)/elans/%.eaf,$(RESULTS_DIR)/%,$(EAF_FILES))

metrics_quality_hfsts: sgh_analyze_stem_word_lat.hfstol translit/cyr2lat.hfstol

metrics_quality: metrics_quality_data
	cat $(METRICS_DIR)/csv/*.csv | grep -v "wordform,tagged" | $(METRICS_DIR)/eval.py -f table \
		--hfst-analyzer sgh_analyze_stem_word_lat.hfstol \
		--hfst-translit translit/cyr2lat.hfstol \
		--details-dir $(METRICS_DIR)/results/total

metrics_quality_pos_%:
	mkdir -p $(METRICS_DIR)/results/pos
	cat $(METRICS_DIR)/csv/*.csv | grep -E "[^,]*,[^,]*<$(subst metrics_quality_pos_,,$@)>" |\
		grep -v "wordform,tagged" | $(METRICS_DIR)/eval.py -f table \
		--hfst-analyzer sgh_analyze_stem_word_lat.hfstol \
		--hfst-translit translit/cyr2lat.hfstol \
		--details-dir $(METRICS_DIR)/results/pos/$(subst metrics_quality_pos_,,$@)

metrics_quality_individual_files: $(DETAIL_DIRS)
$(METRICS_DIR)/results/%: $(METRICS_DIR)/csv/%.csv
	cat $< | grep -v "wordform,tagged" | $(METRICS_DIR)/eval.py -f table \
		--hfst-analyzer sgh_analyze_stem_word_lat.hfstol \
		--hfst-translit translit/cyr2lat.hfstol \
		--details-dir $@

metrics_quality_results_clear:
	rm -r $(RESULTS_DIR)

metrics_quality_data: $(CSV_FILES)
metrics_quality_data_clear: 
	rm $(METRICS_DIR)/csv/*.csv
$(METRICS_DIR)/csv/%.csv: $(METRICS_DIR)/elans/%.eaf
	$(METRICS_DIR)/elan2csv.py $< $@

# Coverage
COVERAGE_DIR := scripts/coverage
metrics_quantity:
	cat $(COVERAGE_DIR)/corpus/* | $(COVERAGE_DIR)/eval.py


########
# Misc #
########

lexicons:
	python3 scripts/lexicons/form_lexd.py

rulemmas:
	python3 scripts/ru_lemmas/process_db_dump.py