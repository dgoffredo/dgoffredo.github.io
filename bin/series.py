'''Group posts together into "series," e.g. "Mexico Trip."'''

import pathutil

import contextlib
import os
import os.path
from pathlib import Path
from xml.etree import ElementTree as ET


def target_name(symlink: Path) -> str:
    """Return the name portion of the path that the specified `symlink` targets."""
    return Path(os.readlink(symlink)).name


def series_navigation(series_dir: Path, page: Path) -> ET.Element:
    """Return a <div> for navigating among the posts referenced in the
    specified `series_dir` for use on the specified `page`.
    """
    assert series_dir.is_dir()
    assert page.exists()
    # Here's the plan:
    # - For each symlink in `series_dir`, note the name of its target (that's
    #   the ISO-8601 date of the post) and its absolute resolved path (that's
    #    the .md source of the post).
    # - Make <a> links to the posts in the series, all relative to
    #   `page.parent`, except for when the post refers to the same page as
    #   `page`: then just use a <span>.  The idea is that you don't link to the
    #   current page.
    navigation = ET.TreeBuilder()

    @contextlib.contextmanager
    def tag(name, attributes):
        yield navigation.start(name, attributes)
        navigation.end(name)

    def text(value: str):
        navigation.data(value)
    
    with tag('div', {'class': 'series-navigation'}):
        with tag('div', {'class': 'series-navigation-header'}):
            text(series_dir.name)
        with tag('div', {'class': 'series-navigation-links'}):
            page_resolved = page.resolve()
            for symlink in sorted(filter(Path.is_symlink, series_dir.iterdir()), key=target_name):
                target = symlink.resolve()
                if target == page_resolved:
                    # This post in the series is the same as the current page.
                    # Use a <span>, not a link.
                    with tag('span', {}):
                        text(symlink.name)
                else:
                    # Link to the post in the series, relative to `page`.  Be
                    # sure to link to the .html page, not the .md (which we're
                    # otherwise using to refer to the post).
                    common = Path(os.path.commonpath([page_resolved, target]))
                    href = (pathutil.up_to(page_resolved, common)/target.relative_to(common)).with_suffix('.html')
                    with tag('a', {'href': str(href)}):
                        text(symlink.name)

    return navigation.close()


def insert_series_navigation(html, series_dir, page):
    """TODO: document
    """
    body = html.find('body')
    assert body is not None, 'need <body> tag to create series navigation'

    container = body.find("div[@class='series-navigation-placeholder']")
    assert container is not None, \
           "Need a <div> with class='series-navigation-placeholder'"

    container.append(series_navigation(series_dir, page))
    return html
