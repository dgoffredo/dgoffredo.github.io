#!/usr/bin/env python3.6

import itertools
import re
import string
from xml.etree import ElementTree as ET

no_punctuation_table = str.maketrans('', '', string.punctuation) 

def linkify(element):
    """Derived from the specified XML `element` two strings suitable for use in
    the text of a hyperlink and in an anchor tag's "name" attribute,
    respectively,  and return the strings.  For example, an
    `xml.etree.ElementTree.Element` that looks like this:

        <h1>This heading has a <em>child    element</em> inside</h1>

    would yield the strings

        This heading has a child element inside

    and

        this_heading_has_a_child_element_inside
    """
    s = ' '.join(element.itertext())      # recursively dredge all text in tree
    text = re.sub(r'\s+', ' ', s)         # collapse contiguous white space
    s = text.lower()                      # lower case
    s = s.translate(no_punctuation_table) # remove punctuation
    name = s.replace(' ', '_')            # replace spaces with underscores
    
    return text, name

def uniquify(name, names):
    """If the string `name` is not in the set `names`, return `name`.
    Otherwise, create a variant based off of `name` that is not in `names`,
    add the variant to `names`, and return the variant.
    """
    candidate = name
    for i in itertools.count(1):
        if candidate in names:
            candidate = f'{name}_{i}'
        else:
            names.add(candidate)
            return candidate

def insert_link_to_anchor(table, name, text):
    table.start('a', {'href': f'#{name}'})
    table.data(text)
    table.end('a')

def insert_table_of_contents(html, max_depth=None):
    """Modify the `html` element tree to contain a table of contents inside of
    its div with class `table-of-contents`.  Add `id` attributes to heading
    tags so that they can be linked to in the table of contents.  The table of
    content will nest headings at most `max_depth` levels deep.  If `max_depth`
    is `None`, then there is no limit.
    """
    table = ET.TreeBuilder()

    body = html.find('body')
    assert body is not None, 'need <body> tag to create table of contents'

    # `levels` is a stack of the hierarchy of N in the appearance of <hN> tags.
    # For example, given this HTML:
    #
    #    <h1 />
    #    <h2 />
    #    <h2 />
    #    <h4 /> <!-- here -->
    #    <h1 />
    #
    # when this function gets to the comment marked "here," the `levels` stack
    # will be `[0, 1, 2, 4]`.  On the next line it will become `[0, 1]`.  There
    # is always a zero at the beginning, and thus `levels` is never empty.
    levels = [0]

    def current_level():
        return levels[-1]

    def set_current_level(level):
        levels[-1] = level

    def parent_level():
        assert len(levels) > 1, 'parent level being examined on initial stack'
        return levels[-2]

    def push_level(level):
        levels.append(level)

    def pop_level():
        levels.pop()

    def depth():
        return len(levels)

    # Each heading will be given a "name" attribute so that it can be linked to
    # in the table of contents.  To make sure each is unique, keep track of
    # those already created.
    names = set()

    # Go through the children of the body tag.  Build up `table` based on any
    # heading tags encountered.  Also, add an `id` attribute to any heading tag
    # encountered, so that the heading can be linked to in `table`.
    for element in body:
        match = re.match(r'h(\d+)', element.tag)
        if not match:
            continue  # not a heading

        # Get an href name and URL text from this heading, and then label the
        # heading so that a link in the table of contents can refer to it.
        text, name = linkify(element)
        name = uniquify(name, names)
        element.set('id', name)

        def start_sibling():
            table.start('li')
            insert_link_to_anchor(table, name, text)

        level = int(match[1])
        if level > current_level():
            # If we haven't reached max depth already, then start a new list
            # indented within the current one.
            if max_depth is None or depth() <= max_depth:
                table.start('ul')
                start_sibling()
                push_level(level)
            continue
        if level == current_level():
            # Close the previous item and create another sibling for it.
            table.end('li')
            start_sibling()
            continue
        while level < current_level():
            if level > parent_level():
                # TODO Dedicate a section near the top of this file explaining
                #      why I have this branch this way.
                #      It handles the case when `h2` is encountered in:
                #
                #          <h1 /> <h3 /> <h3 /> <h2 /> <h3 /> <h1 />
                #
                set_current_level(level)
                start_sibling()
            else:
                # Close the previous item and list, and start a new item.
                table.end('li')
                table.end('ul')
                start_sibling()
                pop_level()

    # Close any open tags in the table of contents, and place it into the body.
    # If we didn't find any headings in this document, then `table` will be
    # empty and we'll get `None`.  In that case, do nothing.
    table_of_contents = table.close()
    if table_of_contents is None:
        return

    container = body.find("div[@class='table-of-contents']")
    assert container is not None, \
           "Need a <div> with class='table-of-contents'"

    container.append(table_of_contents)

def add_table_of_contents(html_text, max_depth=None):
    """Return a string that is `html_text` with a table of contents."""
    debugging = False
    if debugging:
        for i, line in enumerate(html_text.split('\n')):
            print(f'{i:3}: {line}')

    html = ET.fromstring(html_text)
    insert_table_of_contents(html, max_depth)
    return ET.tostring(html, encoding='unicode')

def with_table_of_contents(in_file, out_file, max_depth=None):
    """Add a table of contents to HTML text.

    Read the HTML from the `in_file` file-like object, add a table of contents
    to the HTML, and write the resulting HTML to the `out_file` file-like
    object. Use at most `max_depth` layers of nesting the table of contents, or
    enforce no limit if `max_depth` is `None`.
    """
    html = ET.parse(in_file).getroot()
    insert_table_of_contents(html, max_depth)
    out_file.write(ET.tostring(html, encoding='unicode'))

if __name__ == '__main__':
    import argparse
    import shutil
    import sys

    from pathlib import Path
    from tempfile import NamedTemporaryFile

    parser = argparse.ArgumentParser(
        description='Add a table of contents to HTML.')
    parser.add_argument('--in-place', '-i', action='store_true',
                        help='modify the input file in place')
    parser.add_argument('--depth', '-d', type=int, nargs='?',
                        help='maximum nesting depth in table of contents')
    parser.add_argument('input', nargs='?',
                        help='input HTML file; absent or - for standard input')
    options = parser.parse_args()
   
    use_stdin = options.input is None or options.input == '-'
    if options.in_place and use_stdin:
        print('Must specify an input file if modifying in place.',
              file=sys.stderr)
        sys.exit(1)
 
    in_file = sys.stdin if use_stdin else open(options.input)

    if options.in_place:
        output = NamedTemporaryFile(mode='w', encoding='utf-8', delete=False)
        with_table_of_contents(in_file, output, options.depth)
        in_file.close()
        shutil.move(output.name, in_file.name)
    else:
        with_table_of_contents(in_file, sys.stdout, options.depth)

