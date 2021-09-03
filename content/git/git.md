How Git Works
=============
It's all explained [here][1].

Go ahead. Click the link, and read all of it.  It's not long.

No?

Ok, then.  Here are three of the diagrams from the above link.

Git in Three Diagrams
---------------------
![a tree in git](https://git-scm.com/book/en/v2/images/data-model-2.png)

-----------------------

![multiple trees with commits](https://git-scm.com/book/en/v2/images/data-model-3.png)

-----------------------

![branch pointers](https://git-scm.com/book/en/v2/images/data-model-4.png)

Notice how, in the second diagram, different trees can share file objects and
subdirectory (tree) objects, if those files and subdirectories are exactly the
same (`test.txt` and `d8329f`).

That, to me, is what is so cool about git.  It's not bag of diffs.  It's an
immutable directed graph.

The only thing even resembling diffs in git is the [packfile][2] that it will
create, as an optimization, when the repository becomes very large or needs to
be sent over the network.  Even then, it doesn't use diffs per se, but a clever
encoding that describes objects as data [interspersed with excerpts from other
objects][3].

The next time you're thinking of throwing your laptop out the window out of
frustration with git, just stop to think how pretty it is.

![git logo](git.svg)

[1]: https://git-scm.com/book/en/v2/Git-Internals-Git-Objects
[2]: https://git-scm.com/book/en/v2/Git-Internals-Packfiles
[3]: https://codewords.recurse.com/issues/three/unpacking-git-packfiles
