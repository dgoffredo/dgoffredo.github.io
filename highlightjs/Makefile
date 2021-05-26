.ONESHELL:

# See <https://github.com/highlightjs/highlight.js/releases>
HLJS_VERSION = 10.7.2

.PHONY: all
all: highlight.js default.min.css

default.min.css:
	wget cdnjs.cloudflare.com/ajax/libs/highlight.js/$(HLJS_VERSION)/styles/default.min.css

highlight.js: core.js
	printf "" >$@
	for f in core.js languages/*.js; do
		cat $$f >>$@
		echo >>$@
	done

core.js: pack.js
	# The core code is followed by calls to "registerLanguage," so just stop
	# before the first call to "registerLanguage."
	begin_languages=$$(awk '/^hljs\.registerLanguage/ {print NR; exit}' $<)
	head -$$((begin_languages - 1)) $< >$@

pack.js:
	curl https://cdnjs.cloudflare.com/ajax/libs/highlight.js/$(HLJS_VERSION)/highlight.min.js >$@
	
languages/Makefile:
	curl https://api.github.com/repos/highlightjs/highlight.js/contents/src/languages | \
		jq -r '.[] | select((.name | endswith(".js")) and .type == "file") | .name' | \
		sed 's/\.js$$/.min.js/' | \
		sed 's,^,highlight.js: languages/,' >$@
	
languages/%.js:
	-wget -O$@ https://cdnjs.cloudflare.com/ajax/libs/highlight.js/$(HLJS_VERSION)/languages/$*.js

.PHONY: clean
clean:
	-rm -f languages/* core.js pack.js highlight.js default.min.css

-include languages/Makefile
