"""Wrap certain <img ...> elements in links (<a ...>) to other images.

For example, to turn

    <img src="foo_small.webp"/>

into

    <a href="foo.jpg"><img src="foo_small.webp"/></a>

use

    wrap_images(element, r'^(.*)_small\.webp$', r'\1.jpg')
"""


import re
from xml.etree import ElementTree as ET


def wrap_images(html, src_pattern, href_template):
    """Modify the specified `html` element to wrap all <img> tags whose
    "src" attribute matches the specified `src_pattern` with an <a> tag
    whose "href" attribute is the specified `href_template` in the context
    of the string that matched `src_pattern`.  The relationship between
    `src_pattern` and `href_template` is the same as the "pattern" and
    "repl" arguments to the standard `re.sub` function (`href_template` may
    even be a function). Return `html`, possibly modified in place.
    """
    def visit(parent, child_index, child):
        if child.tag == 'img' and re.match(src_pattern, child.get('src')):
            wrap_image(parent, child, child_index, src_pattern, href_template)
        else:
            for i, grandchild in enumerate(child):
                visit(child, i, grandchild)

    for i, child in enumerate(html):
        visit(html, i, child)
        
    return html


def wrap_image(parent, child, child_index, src_pattern, href_template):
    anchor = ET.TreeBuilder()
    anchor.start('a', {'href': re.sub(src_pattern, href_template, child.get('src'))})
    anchor.end('a')
    anchor = anchor.close()

    anchor.append(child)
    parent.remove(child)
    parent.insert(child_index, anchor)
