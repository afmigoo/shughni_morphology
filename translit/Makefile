.DEFAULT_GOAL := lat2cyr.hfst

lat2cyr.hfst: lat2cyr
	hfst-strings2fst -j -i $< | hfst-repeat -o $@