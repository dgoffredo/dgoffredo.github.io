
svg-targets = $(shell ls content/*.dot | sed 's/dot$$/svg/')

.PHONY: all graphs clean site

all: site

site: clean graphs
	bin/generate

graphs: $(svg-targets)

%.svg: %.dot
	dot -T svg -o $@ $< 

clean:
	bin/clean || (exit 0)