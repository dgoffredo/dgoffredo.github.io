Blog
====
The time has come for me to blog about my blog on my blog.  It's bound to
happen eventually with any hand-coded blog.

I've enjoyed the exercise, because the goal is tangible and easy to state,

> Create a static website generator suitable for programming and travel blogging.

there is no deadline, I am unconstrained by existing code or people, and it's an
opportunity to learn what really goes on underneath premade offerings.

What I've learned is that I'm more of a maker than an engineer, and that I
more value what is created than why it is created.

Static
------
This website is completely static.  The server doesn't generate content on
demand, and there are no client-side scripts.  It's HTML, CSS, and media
(images and videos).  Nothing else. 

If you disable javascript in your browser, the website is unchanged.  If you
disable CSS, the website looks a little bland, but still fine.

There aren't any cookies or modal overlays or scroll-activated banners or
floating menus or asynchonously loaded assets.  It works on your browser, no
matter which browser you use.  There aren't any Google Analytics beacons or
off-screen tracking images.  You won't be asked to sign in with Google, connect
to Facebook, give a thumbs up, or leave a review, and there's no way to tweet,
repost, or add a comment.

It's just HTML, CSS, and media.  My words into the void.

Design
------
The configuration language of the site generator is _the file system_.
```text
.
├── bin
├── config
├── content
├── posts
├── series
├── site
└── Makefile
```
Pages are written in [markdown][1] (`.md`) and placed in the `content/`
directory.  Markdown files will be converted into HTML.  Other types of files
in `content/` will be included in the site verbatim.

The directory structure within `content/` can be whatever you like (e.g. to 
organize pages with their images in directories).

The `posts/` directory contains symbolic links to `.md` files under `content/`.
Each symbol link is a post, and its name is the ISO 8601 date of the post, e.g.
`2021-06-03` for June 3rd, 2021.

The `config/` directory contains pieces of the site that don't vary between
pages, such as the style sheets and the HTML of the navigation bar that appears
at the top and bottom of every page.

The `series/` directory contains one subdirectory per "series."  A series is a
group of related posts, e.g. a series of posts on restoring a car.  The name of
each subdirectory under `series/` is the display name of the series (e.g. 
"Programming Languages"),  and the contents of each such subdirectory are
symbolic links to links in `posts/`, where the name of each symbol link is the
nickname for that post in the series, e.g. "Day 12" in a series on "Peru Trip."
```text
.
├── bin
├── config
│   ├── common.css
│   └── navigate.html
├── content
│   ├── cheesecake.md
│   ├── i-love-scheme.md
│   ├── in_the_oven.jpg
│   └── yay-python.md
├── posts
│   ├── 2021-06-03 -> ../content/yay-python.md
│   ├── 2021-06-09 -> ../content/cheesecake.md
│   └── 2021-07-15 -> ../content/i-love-scheme.md
├── series
│   └── Programming Languages
│       ├── Python -> ../../posts/2021-06-03
│       └── Scheme -> ../../posts/2021-07-15
├── site
└── Makefile
```
The `bin/` directory contains scripts used when generating the site.

The `site/` directory contains the generated static website, where most of the
site's assets are symbolic links to files in `content/` and `config/`.

To generate the site, run `make`.  Then you can run a web server with `site/`
as the domain root, e.g.
```console
$ cd site
$ python3 -m http.server
```
I deploy the site by deep copying `site/` to another directory (no more symbolic
links), and shipping that directory to wherever the blog is hosted.

Implementation
--------------
At first, the code generator was a single python script, [bin/generate][2].

Now it's a [Makefile][3] supported by a menagerie of [scripts][4], and as the
final step of the build a [descendent of bin/generate][5] is called to
copy/link files into `site/`.

The current Frankenstein's monster state of affairs arose gradually, as with
all software projects, due to an accumulation of features implemented by an
inadequately disciplined developer learning things as he went along.

If I could figure out how to end up with cleaner code, documentation, and tests
once I get to this point, I'd be a better developer.

It's a journey!  Now on to the details...

### Accumulated Features
The [commit history][6] tells the story of features added.

- link to page that lists all posts
- style HTML generated from markdown
- generate a table of contents in each post
- highlight syntax in code snippets, using a client-side script
- generate thumbnails for large images (`*_small.*`)
- allow nested directories under `content/`
- support "series" of posts, and generate per-series navigation tables
- link to a page that lists all series
- highlight syntax in code snippets, on the server (no more client-side scripts)
- automatically insert `width` and `height` attributes in `<img>` tags.
- inline CSS (to avoid blocking initial page paint)
- add a mailing list
- add an "API" to facilitate offline scripts related to the mailing list
- add a viewport and tweak styles so that the site looks good on mobile browsers
- use a custom embedded font
- generate an Atom feed (kind of like RSS)

Those are just "user facing" changes.  There was also substantial toil moving
things around, optimizing the generator, writing scripts that generate various
intermediate files, changing how the generated site was structured and
deployed, and packaging the build process into reproducible isolated
environments (like Docker, Guix, and Nix). 

Should have just used Wordpress, right?

Who Gives a Shit?
-----------------
I'm proud enough to say what I ended up with is better and lighter than other
generators out there, but I'm wise enough to know that isn't true.

My static site generator is better than anything else out there for
_generating my site_, and nothing more.  If it had to support the myriad use
cases of even the smallest popular offerings (e.g. [Jekyll][7]), and if my past
development process is any indicator of how it'd go in the future, then what
I'd end up with is a smoldering dumpster fire of bugs, and I'd end up moving
to [Squarespace][8] or something.

If I wanted to do the experiment, I'd clean up (read: rewrite) the code and
market the generator online as "yet another static blog generator," and either
the project would be duly ignored, or unanticipated difficulties encountered
while implementing requested features would ignite the dumpster anew.

In summary: Software is hard. To claim anything else is either arrogance or a
sales pitch.  Still, it's fun.  Look, I made a website!

[1]: https://daringfireball.net/projects/markdown/
[2]: https://github.com/dgoffredo/dgoffredo.github.io/blob/12b499adc0480a55c1bcd34e31ac21f8aa0cd4d0/bin/generate
[3]: https://github.com/dgoffredo/dgoffredo.github.io/blob/master/Makefile
[4]: https://github.com/dgoffredo/dgoffredo.github.io/tree/master/bin
[5]: https://github.com/dgoffredo/dgoffredo.github.io/blob/master/bin/generate
[6]: https://github.com/dgoffredo/dgoffredo.github.io/commits/master
[7]: https://github.com/jekyll/jekyll
[8]: https://www.squarespace.com/
