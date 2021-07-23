Documentation Rant
==================
You've been getting away with it for years, and nobody called you out.

Well, I'm here to call you out.  Your documentation sucks, because you don't
care, and neither does the person who cuts your paychecks.

But I care.  I care so much I could kiss you on the lips.  Here's how you can
improve your documentation.

The Rules
---------
All you need do is follow these six rules.

1. Every source repository has a README file at its root
  that explains first _why_ the code exists, then _what_ it is,
  _how_ to use it, and finally where to learn _more_.

2. Every source repository has a "map" or "tour" that presents an
  overview of the repository's subsystems (e.g. source, utility scripts,
  build systems, continuous integration, documentation generation, etc.).

3. Every subdirectory (every single one) within a source repository
  has a README file that briefly explains what's in that
  directory.  Sometimes it's a file-by-file summary, and sometimes
  it's just a paragraph saying why that directory needs to exist
  (i.e. why the files are there and not elsewhere — what they're for).

4. Every source file has a section at the top that summarizes what the
  file is for, what's in it, and possibly other documentation (e.g.
  example usage).

5. Every subprocedure (function) in a source file has a contract written
  in a human language in a comment.  The contract will also hint at the
  _reason_ for the function's existence, e.g. a note about what other
  code might call the function and why.

6. Every significant "section" of code within a long subprocedure (function)
  is similarly documented.  Better, refactor it into its own subprocedure.

This applies to unit tests as well.  Too often, unit tests are completely
undocumented, or are missing _motivating_ documentation at the top.  No,
the unit tests don't document themselves.  Cut the shit.

This also applies to your steaming piles of YAML, `Dockerfile`, `.gitignore`,
shell scripts, `Makefile`, `CMakeLists.txt`, and anywhere else the real truth
about your system is hiding, undocumented. 

The Critical Bit
----------------
All of this must be kept up to date with the code.  That's the hardest part.

Reading prose and then modifying it to say something slightly different, all
without making an incoherent mess, is hard.  It takes time and concentration
and thought and review.  It doesn't affect compilation, testing, releases,
sales, or promotions.  Do it anyway.  Don't let it get out of date, work
on it!  Do it for me.

Code Modification Checklist
---------------------------
Here's a checklist to help cover your corner cutting ass.

- ✅ Solving the right problem
- ✅ Build succeeds
- ✅ Unit tests succeed
- ✅ Integration tests (automated or manual) succeed
- ✅ Checked whether procedure-level documentation needs alteration/addition
- ✅ Checked whether file-level documentation needs alteration
- ✅ Checked whether directory-level documentation needs alteration
- ✅ Checked whether the repository "tour" needs alteration
- ✅ Checked whether the repository README needs alteration
    
When you add or modify code, find the nodes closest to your changes,
and then for each, trace through all ancestors, checking at each level
whether your changes warrant changes to the documentation at that level.
```text 
 Repo README
   /        \
  /          \
Repo Tour     \
    \_____  Subdirectory README
               /       |
              /        +--- File summary
             /         |     |
  Subdirectory README  |     +--- Procedure contract
          ...          |     |
                       |     +--- Procedure contract
                       |     ...
                       +--- File summary
                       |     ...
                      ...
```

Happy coding!  Remember, your job as a programmer is to _explain systems_.
First to yourself, then to the computer and everyone else.  Don't leave us
hanging.
