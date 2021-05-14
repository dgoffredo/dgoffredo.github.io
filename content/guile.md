Installing Guile from Source
============================
It's not hard, but the [HACKING][1] file doesn't cover it all, so here's the
rest.

Debian Packages
---------------
TL;DR: Do the following.
```console
$ sudo apt install git

$ git clone https://git.sv.gnu.org/git/guile.git

$ cd guile

$ sudo apt install -y \
        autoconf automake libtool gettext flex \
        autopoint libreadline-dev pkg-config libgmp-dev \
        libunistring-dev libgc-dev make gperf texinfo
        
$ ./autogen.sh

$ ./configure

$ make -j 16

$ sudo make install

$ sudo ldconfig

$ guile
```

Now in more detail.

Here are the dependencies mentioned in the [HACKING][1] file:
```console
$ sudo apt install autoconf automake libtool gettext flex
```

Then `./autogen.sh` wants the following, due to the presence of `gettext`:
```console
$ sudo apt install autopoint
```

I wouldn't want to use a REPL without readline support, so install that, too:
```console
$ sudo apt install libreadline-dev
```

`./configure` will complain unless all of the following are installed:
```console
$ sudo apt install pkg-config libgmp-dev libunistring-dev libgc-dev
```

Then of course you need `make`, but also `gperf` (for some reason) and
`texinfo` for documentation:
```console
$ sudo apt install make gperf texinfo
```

Installation
------------
After `sudo make install`, guile will be installed under `/usr/local/`, but
will fail to run until you first refresh the loader's knowledge of where
shared objects are:
```console
$ sudo ldconfig
```

Finally, guile is ready:
```console
$ guile
GNU Guile 3.0.6.7-3bce5
Copyright (C) 1995-2021 Free Software Foundation, Inc.

Guile comes with ABSOLUTELY NO WARRANTY; for details type `,show w'.
This program is free software, and you are welcome to redistribute it
under certain conditions; type `,show c' for details.

Enter `,help' for help.
scheme@(guile-user)> 
```

[1]: https://git.savannah.gnu.org/cgit/guile.git/tree/HACKING
