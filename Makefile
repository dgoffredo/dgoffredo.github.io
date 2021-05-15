# Some conveniences.  See <https://tech.davis-hansson.com/p/make/>
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

markdowns := $(shell find content/ -type f -name '*.md')

.PHONY: clean

site/index.html: $(shell find content/) bin/generate
	rm -rf site/*
	bin/generate

# Dependencies of a markdown file can be deduced by a script.
# The output file (*.d) adds make dependencies to site/index.html.
# The make dependencies are included at the bottom of this file.  Those
# dependencies so added will then be made according to their recipes (e.g.
# %_small.jpg).
%.md.d: %.md bin/dependencies
	bin/dependencies $< >$@

# Create PNG images from graphviz files (.dot files)
%.dot.png: %.dot
	dot -T png -o $@ $< 

# Set width of small images to 700 pixels, scaling the height proportionally.
%_small.jpg: %.jpg bin/shrink
	bin/shrink $< $@

clean:
	rm -rf site/*
	find content/ -type f -name '*_small.jpg' -exec rm {} \;
	# no, some are missing .dot sources: find content/ -type f -name '*.dot.png' -exec rm {} \;

# Include dependencies parsed from input markdown files,
# e.g. links to *_small.jpg, *.dot.png
include $(markdowns:.md=.md.d)
