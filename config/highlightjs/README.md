highlightjs
===========
This is a modified version of a release of highlightjs.  I didn't change any of
the source code or the styles, I just paste things together so that I have a
node-compatible `hljs` object that knows about all of the languages.  The
[style sheet][1] is the default style.

The list of [languages][2] is derived from the github source using github's
"contents API" (each language is some `.js` file in a particular directory in
the source code).  Then a corresponding `.js` file is downloaded from a CDN
for each language.  The version of highlightjs used when fetching the scripts
and the style sheet are the same -- see the relevant variable in the
[Makefile][3].

The list of languages is derived from the languages supported by the
highlightjs source's master branch, while the corresponding release artifacts
are based on some release version.  Thus it's likely that some of the files
will fail to download (HTTP 404) due to having been added to the source since
the release.  This is fine.

A clean build calls `wget` many times -- you'll want to use `make -j` or similar.

[1]: default.min.css
[2]: languages/
[3]: Makefile
