SHELL = /bin/bash

tex = *.tex
figs = figs/**/*.pdf
results = figs/**/*.pdf
sources = $(tex) $(figs) $(results)

prefix   = main
main     = $(prefix).tex
pdf      = $(prefix).pdf

diff_dir  = diffs
diff_orig = $(diff_dir)/$(prefix).expanded.orig.tex
diff_new  = $(diff_dir)/$(prefix).expanded.tex
diff_tex  = $(diff_dir)/$(prefix).diff.tex
diff_pdf_prefix = $(diff_dir)/$(prefix).diff
diff_pdf  = $(diff_pdf_prefix).pdf

.PHONY: default
default:pdf

.PHONY: pdf
pdf: $(pdf)

$(pdf): $(sources)
	latexmk -pdf -f $(main)

$(diff_new): $(sources)
	latexpand $(main) -o $(diff_new)

$(diff_tex): $(diff_new)
	latexdiff $(diff_orig) $(diff_new) > $(diff_tex)

$(diff_pdf): $(diff_tex)
	latexmk -pdf -f -cd- $(diff_tex) -jobname=$(diff_pdf_prefix)

.PHONY: diff
diff: $(diff_pdf)

.PHONY: clean
clean:
	latexmk -C
	pushd diffs; latexmk -C; popd

.PHONY: mrproper
mrproper: clean
	git clean -Xf
