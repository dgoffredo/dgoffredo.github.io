#!/usr/bin/env python3

"""Use highlightjs to highlight code in an `ET.Element` tree.

This module looks for `<pre><code>... </code></pre>`
subtrees within a specified `ET.Element` and converts them into
`<pre><code><span class="..."> ... </code></pre>` using an external
nodejs script that utilitizes the highlightjs javascript library.

Language hints are taken from the `class` attribute of the `<code>` tag,
or otherwise the language is deduced from the inline code itself.
"""


import functools
import io
import json
from pathlib import Path
import re
from subprocess import Popen, PIPE
from typing import Optional
from xml.etree import ElementTree as ET


@functools.lru_cache(maxsize=None)
def highlightd():
    exe = str((Path(__file__)/'..'/'highlightd').resolve())
    return Popen([exe], encoding='utf8', stdin=PIPE, stdout=PIPE, bufsize=0)


def highlight_string(code: str, language: str = None) -> ET.Element:
    """Return a <code> `Element` containing HTML markup that is a syntax
    colored version of the specified `code`, which is the optionally specified
    `language`.  The `language` name is any recognized by the highlightjs
    Javascript library.  If `language` is `None`, then it is deduced from
    `code`.
    """
    command = {'code': code}
    if language is not None:
        command['language'] = language

    highlightd().stdin.write(json.dumps(command) + '\n')
    result = highlightd().stdout.readline().rstrip()
    result = json.loads(result)

    markup = result['markup']
    # Wrap the markup in a <code> so that there's one root element.
    return ET.fromstring(f'<code>{markup}</code>')


def language(element: ET.Element) -> Optional[str]:
    """Return a source language name deduced from the `class` attribute of the
    specified `element`.
    """
    classes = element.get('class', '').split()
    # Return the first one that matches.
    for css_class in classes:
        match = re.match(r'(lang|language)-(.*)$', css_class)
        if match is not None:
            prefix, language = match.groups()
            return language


def highlight_element(code: ET.Element) -> ET.Element:
    """Return the specified `code` <code> element, modified in place to have
    source code contained within it highlighted using highlightjs.
    """
    assert len(code) == 0 # no children initially, just text

    deduced_language = language(code)
    highlighted_code = highlight_string(code.text, deduced_language)
    
    # add "hljs" to the <code>.class
    code.set('class', ' '.join(code.get('class', '').split() + ['hljs']))
    
    # Give `code` the same initial text and children as `highlighted_code`.
    code.text = highlighted_code.text
    code.extend(highlighted_code)
    return code


def highlight_code_blocks(html: ET.Element) -> ET.Element:
    """TODO: document
    """
    def visit(parent, element):
        if parent.tag == 'pre' and element.tag == 'code':
            highlight_element(element)
            return

        # Otherwise, recur into children.
        for child in element:
            visit(element, child)

    for child in html:
        visit(html, child)   

    return html


def highlight_html(source) -> str:
    html = ET.fromstring(f'<root>{source.read()}</root>')
    highlight_code_blocks(html)

    buffer = io.StringIO()
    # Could specify `method='html'`, but I want to be able to parse the
    # output again as XML (e.g. to add a <base> tag to index.html).
    # `short_empty_elements=False` is so far the sweet spot for
    # HTML-compatible XML output, at least for this site.
    ET.ElementTree(html).write(buffer, encoding='unicode', short_empty_elements=False) 

    # Strip the <root> tags from the result (we added them above to ensure
    # that `ET.fromstring` saw a complete tree).
    return buffer.getvalue()[len('<root>'):-len('</root>')]


if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='''\
Highlight <pre><code> blocks in HTML.
Print the highlighted result to standard output.''')
    parser.add_argument('--in-place', action='store_true',
        help="modify the input file in-place (can't be standard input)")
    parser.add_argument('file', nargs='?', default='-',
        help='path to input HTML, or "-" for standard input')

    options = parser.parse_args()
    if options.file == '-':
        output = highlight_html(sys.stdin)
    else:
        with open(options.file) as file:
            output = highlight_html(file)

    if options.in_place:
        with open(options.file, 'w') as file:
            file.write(output)
    else:
        sys.stdout.write(output)
