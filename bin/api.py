"""Create JSON files accessible under /api/ in the site."""


import atom
from xml.etree import ElementTree as ET
import json
from pathlib import Path


_index_html = """\
<html>
  <head><title>Application Programming Interface (API)</title></head>
  <body>
    <h1>Application Programming Interface (API)</h1>
    <p>The resources under <code>/api/</code> facilitate programmatic interaction with the site.</p>
    
    <h2>GET</h2>
    <dl>
      <dt><code>/api/newest.json</code></dt>
      <dd>The most recent post. Returns: <pre><code>{
    "date": string (ISO-8601 YYYY-MM-DD),
    "title": string,
    "href": string (in-domain link, e.g. "/foo/bar.html")
}</code></pre>
      </dd>

      <dt><code>/api/atom.xml</code></dt>
      <dt><code>/feed</code></dt>
      <dd>An <a href="https://en.wikipedia.org/wiki/Atom_(Web_standard)">Atom</a> feed for the blog.</dd>

      <!-- Add new elements here -->

      <dt><code>/api/</code></dt>
      <dt><code>/api/index.html</code></dt>
      <dd>This page.<dd>
    </dl>
  </body>
</html>
"""


def create_api(posts_list, page_titles, site: Path, content: Path):
    """Create JSON files accessible under /api/ in the site."""
    api = site/'api'
    api.mkdir()

    # index.html, which is documentation
    (api/'index.html').write_text(_index_html)

    # most recent post ("newest")
    markdown_path, post_date = posts_list[0]
    (api/'newest.json').write_text(json.dumps({
        'date': post_date.isoformat(),
        'title': page_titles[markdown_path],
        'href': '/' + str(markdown_path.relative_to(content).with_suffix('.html'))
    }))

    # Atom feed
    feed = atom.create_feed(posts_list, page_titles, content)
    ET.ElementTree(feed).write(api/'atom.xml', encoding='unicode')
    (site/'feed').symlink_to(api/'atom.xml')
