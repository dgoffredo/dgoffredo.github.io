"""pathlib.Path functions not in the standard library"""


from pathlib import Path


def up_to(descendant, ancestor):
    """Return a relative path of multiple ".." that describes the specified
    `descendent` file in terms of its specified `ancestor` directory, e.g.
    `up_to(Path('foo/bar/baz/thing.txt', 'foo'))` is `Path('../..')`.
    """
    assert not descendant.is_dir()
    assert descendant.parts[:len(ancestor.parts)] == ancestor.parts

    result = Path('.')
    for _ in range(len(descendant.parent.parts) - len(ancestor.parts)):
        result = result/Path('..')

    return result
