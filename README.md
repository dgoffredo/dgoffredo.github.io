dgoffredo.github.io
===================
Here's a bare-bones hand-written blog generator.  I use it to create
[my blog][3].

Why
---
I want to learn the mistakes of writing a static website generator.

What
----
A python script that pastes together a static HTML website based on input
markdown in a particular directory structure.

How
---
Put markdown files in `content/`, create symlinks to them in `posts/`, where
each symlink has a name like `YYYY-MM-DD`, e.g. `2018-01-07`, and then run
`make` in the repository directory.

The generator requires python3.6+ and the following `apt` packages (or their
equivalents on other systems):
```console
$ sudo apt install graphviz imagemagick make coreutils
```

Additionally, the generator requires [Node.js][1], which I use [nvm][2]
(Node Version Manager) to manage.  The generator was most recently
tested using
```console
$ node --version
v14.16.1
```

More
----
### Series
At first this was a programming blog, but before long I was using it to blog
about my travels.  A series of posts on a related topic, such as "Mexico Trip,"
can be logically grouped together by adding a subdirectory to the
[series/](series) directory.  See the [readme](series/README.md) in that
directory for more information.

[1]: https://nodejs.org
[2]: https://github.com/nvm-sh/nvm
[3]: https://www.davidgoffredo.com