"""Create JSON files accessible under /api/ in the site."""


import json
from pathlib import Path


def create_api(posts_list, page_titles, site: Path, content: Path):
    """Create JSON files accessible under /api/ in the site."""
    api = site/'api'
    api.mkdir()

    # most recent post ("newest")
    markdown_path, post_date = posts_list[0]
    (api/'newest.json').write_text(json.dumps({
        'date': post_date.isoformat(),
        'title': page_titles[markdown_path],
        'href': '/' + str(markdown_path.relative_to(content).with_suffix('.html'))
    }))
