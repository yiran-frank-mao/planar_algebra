LATEX ?= pdflatex
LATEXFLAGS = -interaction=nonstopmode -halt-on-error
export TEXINPUTS := $(CURDIR)//:$(TEXINPUTS)

.PHONY: all doc examples test clean

all: doc examples

doc: planaralgebra-doc.pdf

examples: examples/tangles.pdf

planaralgebra-doc.pdf: planaralgebra-doc.tex planaralgebra.sty
	$(LATEX) $(LATEXFLAGS) $<
	$(LATEX) $(LATEXFLAGS) $<

examples/tangles.pdf: examples/tangles.tex planaralgebra.sty
	cd examples && $(LATEX) $(LATEXFLAGS) tangles.tex

test:
	python3 tests/check_reduce.py 1
	python3 tests/check_reduce.py 2
	python3 tests/check_standalone.py

clean:
	rm -f *.aux *.log *.out *.toc examples/*.aux examples/*.log tests/*.aux tests/*.log
