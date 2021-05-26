"""Add height attributes to `<img>` tags that refer to a local image.

For example, if `content/mexico/mexico3.md` includes an image with
`href="mexico_23_small.jpg"`, then this module will fork to an imagemagick
tool (`identify`) to determine the image's height and then modify the relevent
`ElementTree.Element` to be `<img src="mexico_23_small.jpg" height="933" />`.
"""


from pathlib import Path
import subprocess
from typing import Optional
from urllib.parse import urlparse
from xml.etree import ElementTree as ET


def resolve_path_to_image(src: str, content_dir: Path, markdown: Path) -> Optional[Path]:
    """Return an absolute path to the image referenced by the specified
    `markdown` file via the specified <img> `src` attribute, where `content_dir`
    is an absolute path to the content/ directory of this repository.  `markdown`
    must also be an absolute path.  If `src` does not refer to a local file,
    return `None`.
    """
    assert content_dir.is_absolute()
    assert markdown.is_absolute()
    assert markdown.exists()
    assert not markdown.is_dir()

    # `src` has schema? skip (return None)
    # `src` is absolute path? relative to content/
    # `src` is relative path? relative to directory of the .md file
    
    url = urlparse(src)
    if url.scheme:
        return # http, ftp, etc. not a local path
    
    src_path = Path(url.path)
    if src_path.is_absolute():
        # Absolute paths are relative to the website root.  During the build,
        # use content/ instead of site/, since not all files from content/
        # necessarily will have been linked/written into site/ at this point in
        # the build.
        return content_dir/src_path.relative_to(src_path.root)

    # `src_path` is relative (to the directory that `markdown` is in)
    return markdown.parent/src_path


def calculate_height(image: Path) -> int:
    script = Path(__file__).parent/'height'
    command = [script, str(image)]
    result = subprocess.run(command, encoding='utf8', capture_output=True)

    # If `image` is an animated GIF, then the script will print the height of
    # each frame.  So, allow for that possibility, and use the height of the
    # first frame, which I've found empirically is the "real height" of the
    # GIF.
    heights = [int(chunk) for chunk in result.stdout.split()]
    assert len(heights) > 0
    return heights[0]


_heights_cache = {} # absolute Path -> int


def height(image: Path) -> int:
    assert image.is_absolute()
    
    cached_value = _heights_cache.get(image)
    if cached_value is not None:
        return cached_value

    calculated_value = calculate_height(image)
    _heights_cache[image] = calculated_value
    return calculated_value


def add_height_attribute(img: ET.Element, content_dir: Path, markdown: Path) -> ET.Element:
    """Return the specified `img` modified in place to include a "height"
    attribute that is the height of the image named in its "src."
    """
    assert content_dir.is_absolute()
    assert markdown.is_absolute()
    assert img.tag == 'img'
    assert img.get('src') is not None

    image = resolve_path_to_image(img.get('src'), content_dir, markdown)
    if image is None:
        return img # nothing to do; the src is an external URL
    
    img.set('height', str(height(image)))
    return image


def add_height_attributes(html: ET.Element, content_dir: Path, markdown: Path) -> ET.Element:
    """Walk the specified `html` tree adding "height" attributes to all
    applicable <img> elements.  Return `html`, possibly modified in place.
    """
    assert content_dir.is_absolute()
    assert markdown.is_absolute()
    
    def visit(element: ET.Element):
        if element.tag == 'img':
            add_height_attribute(element, content_dir, markdown)
            return
        
        for child in element:
            visit(child)
    
    visit(html)
    return html
