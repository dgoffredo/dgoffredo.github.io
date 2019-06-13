
graph-targets = $(shell ls content/*.dot | sed 's/dot$$/dot.png/')

.PHONY: all graphs clean site

all: site

site: clean graphs
	bin/generate

graphs: $(graph-targets)

%.dot.png: %.dot
	dot -T png -o $@ $< 

clean:
	bin/clean || (exit 0)