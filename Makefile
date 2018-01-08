
.PHONY:
all:
	bin/clean || (exit 0)
	bin/generate
