dgoffredo.github.io
===================
Here's a bare-bones hand-written blog generator.  I use it to create
[my blog](https://dgoffredo.github.io/).

Why
---
I will resist web things.

What
----
A python script that pastes together a static HTML website based on input
markdown in a particular directory structure.

How
---
Put markdown files in `content/`, create symlinks to them in `posts/`, where
each symlink has a name like `YYYY-MM-DD`, e.g. `2018-01-07`, and then run
`make` in the repository directory.

The generator requires python3.6+.

More
----
See the python script [bin/generate](bin/generate).
