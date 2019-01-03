
.PHONY: all

all: $(shell ls *.dot | sed 's/dot$$/png/')

%.png: %.dot
	dot -T png -o $@ $<