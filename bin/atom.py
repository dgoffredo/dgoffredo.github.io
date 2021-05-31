"""Atom feed (it's like RSS)"""


import datetime
import mistune
from pathlib import Path
from xml.etree import ElementTree as ET
import sxml


_markdown_converter = mistune.Markdown(use_xhtml=True)


def create_feed(posts_list, page_titles, content: Path) -> ET.Element:
    # `posts_list` is sorted newest-first, so the first date is the
    # "update time" (date, really) of the blog.
    _, updated_date = posts_list[0]

    site = 'https://www.davidgoffredo.com'

    return sxml.element_from_sexpr(
        ['feed', {'xmlns': 'http://www.w3.org/2005/Atom'},
            ['title', 'A Programming Blog'],
            ['link', {'href': site}],
            ['updated', updated_date],
            ['author',
                ['name', 'David Goffredo']],
            ['id', site + '/feed'],
            *[entry_sexpr(markdown, date, page_titles[markdown], content, site) \
              for markdown, date in posts_list]])


def entry_sexpr(markdown: Path, date: datetime.date, title: str, content: Path, site: str) -> list:
    href = f'{site}/{markdown.relative_to(content).with_suffix(".html")}'
    raw_xhtml = _markdown_converter(markdown.read_text())
    xhtml = ET.fromstring(f'<div>{raw_xhtml}</div>')

    return ['entry',
        ['title', title],
        ['link', {'href': href}],
        ['id', href],
        ['updated', date],
        ['content', {'type': 'xhtml'},
            ['div', {'xmlns': 'http://www.w3.org/1999/xhtml'},
                xhtml]]]


# For reference, here's an example feed:
"""
<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">

  <title>Example Feed</title>
  <link href="http://example.org/"/>
  <updated>2003-12-13T18:30:02Z</updated>
  <author>
    <name>John Doe</name>
  </author>
  <id>urn:uuid:60a76c80-d399-11d9-b93C-0003939e0af6</id>

  <entry>
    <title>Atom-Powered Robots Run Amok</title>
    <link href="http://example.org/2003/12/13/atom03"/>
    <id>urn:uuid:1225c695-cfb8-4ebb-aaaa-80da344efa6a</id>
    <updated>2003-12-13T18:30:02Z</updated>
    <summary>Some text.</summary>
  </entry>

</feed>
"""
