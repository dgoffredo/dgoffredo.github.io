
graph-targets := $(shell ls content/*.dot | sed 's/dot$$/dot.png/')

sed-expression := s,.*\<site/\([^/]\+_small\.jpg\)\>.*,content/\1,p
shrunk-images := $(shell sed -n '$(sed-expression)' content/*.md)

.PHONY: graphs clean

index.html: $(graph-targets) $(shrunk-images) content/*
	rm -f site/*
	bin/generate

# This rule will be used for $(graph-targets)
%.dot.png: %.dot
	dot -T png -o $@ $< 

# This rule will be used for $(shrunk-images)
# Set width of small images to 700 pixels, scaling the height proportionally.
%_small.jpg: %.jpg
	bin/shrink $< $@

clean:
	rm -f site/*
	rm -f content/*_small.jpg
	rm -f content/*.dot.png
