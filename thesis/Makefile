prefix = main
main   = $(prefix).tex

diff_dir  = diffs
diff_orig = $(diff_dir)/$(prefix).expanded.orig.tex
diff_new  = $(diff_dir)/$(prefix).expanded.tex
diff_tex  = $(diff_dir)/$(prefix).diff.tex
diff_pdf  = $(diff_dir)/$(prefix).diff.pdf

.PHONY: default
default: diff

$(diff_new):
	latexpand $(main) -o $(diff_new)

$(diff_tex): $(diff_new)
	latexdiff $(diff_orig) $(diff_new) > $(diff_tex)

$(diff_pdf): $(diff_tex)
	latexmk -pdf -f -cd- $(diff_tex) -o $(diff_pdf)

.PHONY: diff
diff: $(diff_pdf)
