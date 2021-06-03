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

The generator requires python3.7+ and the following `apt` packages (or their
equivalents on other systems):
```console
$ sudo apt install \
    ca-certificates \
    coreutils \
    findutils \
    gawk \
    graphviz \
    imagemagick \
    jq \
    make \
    nodejs \
    python3 \
    sed \
    webp \
    wget
```

Alternatively, you can build the site using a self-contained environment
provided by either of [Guix][4] or [Docker][5].

### Guix
Run [guix-build](bin/guix-build) to build the website.  It creates an ad-hoc 
environment with this repository mounted in it, and then runs `make`.

There are a couple of hacks in there to work around a bug in Guix's imagemagick
package and various quirks in Guix.

### Docker
Run [docker-build](bin/docker-build).  It creates a Debian image called 
`blog-build-env`, which then has this respository mounted into it before
running `make`.

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
[4]: https://guix.gnu.org/
[5]: https://www.docker.com/
