all: num.analyzer.hfst num.generator.hfst
	hfst-fst2strings num.generator.hfst

num.analyzer.hfst: num.generator.hfst
	hfst-invert num.generator.hfst -o num.analyzer.hfst

num.generator.hfst: num.lexd
	lexd num.lexd | hfst-txt2fst -o num.generator.hfst