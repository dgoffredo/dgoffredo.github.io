
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

# TODO Just playing with it.
if __name__ == '__main__':
    from sys import argv
    path = '../site/pedant-cheat-sheet.html' if len(argv) < 2 else argv[1]
    html = ET.parse(path).getroot()
    insert_table_of_contents(html, max_depth=2)
    print(ET.tostring(html, encoding='unicode'))
