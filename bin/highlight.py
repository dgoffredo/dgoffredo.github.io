"""Use highlightjs to highlight code in an `ET.Element` tree.

This module looks for `<pre><code>... </code></pre>`
subtrees within a specified `ET.Element` and converts them into
`<pre><code><span class="..."> ... </code></pre>` using an external
nodejs script that utilitizes the highlightjs javascript library.

Language hints are taken from the `class` attribute of the `<code>` tag,
or otherwise the language is deduced from the inline code itself.
"""


import functools
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
    