"""Inline style sheets (CSS) into a parsed tree of HTML"""


import functools
from pathlib import Path
from urllib.parse import urlparse
from xml.etree import ElementTree as ET


def inline_styles(html: ET.Element, config_dir: Path) -> ET.Element:
    """Inline or remove style sheets from the specified `html`.
    Return `html`, possibly modified in place.  The specified `config_dir` is an
    absolute path to the config/ directory of this repository.
    """
    assert config_dir.is_absolute()
    
    def visit(parent: ET.Element, element: ET.Element):
        if element.tag == 'link' and element.get('rel') == 'stylesheet':
            if element.get('href').startswith('/highlightjs/'):
                # See whether we need code highlighting.  If so, inline the
                # style sheet.  If not, remove the element.
                # The highlightjs style sheet is also different from the others,
                # because it doesn't live in the config/ directory.
                if html.find('.//code') is None:
                    # No <code> tags, so we don't need the highlightjs styles.
                    parent.remove(element)
                else:
                    inline_style(element, config_dir.parent)
            else:
                inline_style(element, config_dir)
        else:
            # Not a style sheet link.  Keep crawling.
            for child in element:
                visit(element, child)
            
    for child in html:
        visit(html, child)
    

def inline_style(link: ET.Element, styles_dir: Path) -> ET.Element:
    """Modify the specified style sheet `link` to instead be a <style> element
    containing the style sheet inline.  Return `link`, modified in place.
    The specified `styles_dir` is an absolute path to the directory of styles.
    """
    assert styles_dir.is_absolute()
    assert styles_dir.exists()
    assert styles_dir.is_dir()
    
    url = urlparse(link.get('href'))
    if url.scheme:
        # This is a real link, not some local file path.  Leave it.
        return link

    path = Path(url.path)
    assert path.is_absolute()
    
    style = styles_dir/path.relative_to(path.root)

    # Wipe out the <link> element and make it a <style> element with the
    # contents of the style sheet inline.
    link.clear()
    link.tag = 'style'
    link.text = read_style(style)
    return link


@functools.cache
def read_style(path: Path) -> str:
    return path.read_text()
