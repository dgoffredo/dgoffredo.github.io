```
(define sum
  (λ (args ...)
    (+ args ...)))

(define (sum args ...)
  (+ args ...))

(define-as (list 1 2 third _ ...) (something "foo"))

{key value key2 value2}

[value value2 value3]

(let (foo bar
      baz buzz)
  whatever)

(match value
  pattern template
  pattern2 template2)
```

The Language That I Think I Want
================================
- but probably don't
- and certainly don't need

I'm one of those nerds who likes to opine about programming languages.

From an industry perspective, it's an all-too-common Big Waste of Time, but boy
is it fun.  It's like having strong opinions about fonts, except that the
fonts can move mountains.  Digital mountains, of course.

Observations
------------
- Scheme is all anybody needs, but it sucks to always start from scratch
- C is all anybody needs, but it sucks to always start from scratch
- Go is all anybody needs, but it sucks to always start from scratch
    - Well, that's not so fair.  Go has a useful standard library.
    - I know that complaining about the lack of generics is a cliche
        - but come on!
        - won't even compare lists, that's where I draw the line
- Maybe I should try OCaml.  They've been telling me for years...
- Programming languages grow in scope and complexity as they age
    - embrace it, simplicitly is dead!
    - maybe FORTRAN '22 _should_ have built-in SMTP.  Might be useful!

Aims
----
The _reason_ for this exercise is to end up at:

    $ mkdir solveproblem
    $ cd solveproblem
    $ vim somefile.language
    [... write a small amount of non-arcane code ...]
    $ sometool
    $ ./solveproblem
    $ xdg-open beer

Maybe you're thinking "Perl."  I'm thinking more of something:

- Like Scheme, but borrowing some conveniences from Clojure:
    - literal data structures (vectors, lists, dictionaries, sets)
    - immutable by default
    - fewer parentheses
    - no cons cells
    - **functions act on interfaces, not on concrete types**
- Scheme is so good because regular syntax, homoiconic, programmable...
    - ... blah blah BLAH DRINK THIS KOOL-AID
    - let's be honest, we're just doing this for the parentheses
    - so smooth, aesthetically pleasing, perfectly balanced, very nice
- More pattern matching:
    - in function definitions, let bindings
    - like ES6 destructuring, but with Scheme's pattern matching
- File system based packages, maybe something like in Python
    - no special `tool init`, no special `.module`, etc.
- Reduced variety of primitive types
    - only one type of number (decimal!), one text encoding, no char
    - scary compatibility and performance implications, YOLO!
- Hygienic macro system, maybe something like Racket's syntax-parse
- "Batteries included" library support, e.g.:
    - POSIX equivalents (a lot: file systems, sockets, clock, poll, etc.)
    - Python-compatible regular expressions
    - random number generation
    - ... maybe what I want is just [Hy][2] :)
        - or [ClojureScript on node][3]?
            - I'll do a project in those languages first...
    - command line parsing
    - all the algorithms (e.g. STL)
    - database inter-op
    - sqlite (life is too short not to have sqlite)
- a simple, non-opaque system for record types and interfaces
    - maybe like Go, or maybe just use duck typing (like Python)
    - Crockford's "class-free object oriented programming" is tempting,
      except that I think a checked interface (whether dynamic or static)
      is beneficial enough to be part of the language.
- date/time and time zones that just work and don't let you get it wrong
    - ISO-8601 built in
- built-in concurrency
    - Go's approach is so compelling, I think that's the way
    - might be better suited as a library, like Guile's fibers.  Not sure.
        - oh yeah, and if we do CSP, let it be based on CML
- macros or special syntax for comprehensions
    - Racket's `(for/list ...)`  is pretty good.  Maybe even more concise.
    - hard to do better than Python or Haskell style comprehensions

TBD
---
- How much like Scheme with regard to control flow?
    - call/cc?
    - dynamic-unwind?
    - maybe something more like exceptions?
    - or maybe errors as values? (e.g. Go)
    - or maybe dedicated error syntax as _part_ of the call syntax?
        - what could that look like?
- assertions?
- foreign function interface?
- "unsafe" library? (for memory access, syscalls, etc. a la Go)

Conclusions
-----------
- There's nothing new here, really.
- This synthesis is probably not going to produce anything substantially
  better than what's currently available, except that it will all fit in
  my head (and nobody else's).
- Maybe I should just pick a subset of Racket and write in that
    - or, HEY, I could implement all of this as a Racket `#lang`
    - that'd be a worthwhile exercise all on its own
    - 🤩
    - it's the [lisp curse][1]!

[1]: http://winestockwebdesign.com/Essays/Lisp_Curse.html
[2]: https://docs.hylang.org/en/stable/
[3]: https://github.com/anmonteiro/lumo
