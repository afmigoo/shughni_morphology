.DEFAULT_GOAL := num.analyzer.hfst

num.analyzer.hfst: num.generator.hfst
	hfst-invert $< -o $@
num.generator.hfst: num.lexd
	lexd $< | hfst-txt2fst -o $@

test.pass.txt: tests.csv
    awk -F, '$$3 == "pass" {print $$1 ":" $$2}' $^ | sort -u > $@
check: and.noun.generator.hfst test.pass.txt
    bash compare.sh $^
clean: check
    rm test.*