Anonymous Recursion
================== 
I've been reading _[Denotational Semantics][1]_, a textbook describing a theory
of programming languages.  It was recommended to me years ago by a
colleague.  He said something along the lines of "this book taught me
everything I know about programming."  He seemed to know a lot about
programming.

The first few sections introduce a formula rewriting system known as the
[lambda calculus][2], which was familiar to me due to my previous dabbling with
[Scheme][3], a programming language invented to study the lambda calculus.

In particular, one of the ideas introduced in the lambda calculus section of
_Denotational Semantics_ is illustrated differently in another book I read,
_[The Little Schemer][4]_.  The idea is how an anonymous procedure can
nonetheless refer to itself by name.

This post is my attempt to explain that idea.

Scheme
------
Instead of using the lambda calculus, I'll use Scheme.  I like Scheme.

Here's the definition of a procedure:
```scheme
(define collatz-end
  (λ (n)
    (cond
      [(= n 1) 1]
      [(even? n) (collatz-end (/ n 2))]
      [(odd? n) (collatz-end (+ 1 (* 3 n)))])))
```
Here `n` is any nonzero [natural number][5], so `n` could be any of 1, 2, 3, 4, ...,
44989933, etc., but not -4, and not 0.

The procedure `collatz-end` is equivalent to the following procedure, provided
that the [Collatz conjecture][6] is true:
```scheme
(λ (n) 1)
```
The Collatz conjecture is almost certainly true, but it might be impossible to
prove.

Anyway, in Scheme, `(λ (x) Expr)` is a procedure of one parameter, `x`, that
evaluates to whatever `Expr` would be if `x`s within it were substituted for
whatever we supplied for `x`.

For example, `(λ (x) (+ 3 x))`, when applied to `7`, is `(+ 3 7)`, which is
`10`.  The expression that says "apply `(λ (x) (+ 3 x))` to `7`" is the
procedure and its argument next to each other in parentheses.  So,
`((λ (x) (+ 3 x)) 7)` is `(+ 3 7)` is `10`.

It's a bit trickier than that, though, because the body of the `λ` could
contain other `λ`s, and those might introduce a parameter called `x`, too.  In
that case, the inner `x` is really a different `x` from our `x`, and so we'd
have to rename one of them to accommodate the other.  Let's not worry about
that here.

`cond` is a shorthand for nested `if` expressions.  An `if` expression has
the form
```scheme
(if Predicate Consequent Alternative)
```
Each of `Predicate`, `Consequent`, and `Alternative` is an arbitrary expression.
If the result of evaluating `Predicate` is _not falsy_ (I won't bother
describing falsiness in Scheme), then the value of the `if` expression is the
result of evaluating `Consequent`.  In that case, `Alternative` is not evaluated.
On the other hand, if the result of evaluating `Predicate` _is falsy_, then
the value of the `if` expression is the result of evaluating `Alternative`.  In that
case, `Consequent` is not evaluated.

`cond`, then, is just a macro that nests its `[Predicate Consequent]` arguments.
I'll define it here using [syntax-rules][7]:
```scheme
(define-syntax cond
  (syntax-rules (else)
    [(cond)
     (raise-user-error "Unmatched cond alternative")]

    [(cond [else expr])
     expr]

    [(cond [predicate expr] rest ...)
     (if predicate expr (cond rest ...))]))
```
Note that square brackets (`[]`) and parentheses (`()`) have the same meaning,
and are varied as a matter of style.

Now let's look at the definition of `collatz-end` again:
```scheme
(define collatz-end
  (λ (n)
    (cond
      [(= n 1) 1]
      [(even? n) (collatz-end (/ n 2))]
      [(odd? n) (collatz-end (+ 1 (* 3 n)))])))
```
If `n` is `1`, then we finish at `1`.  If instead `n` is any even number, then
we divide `n` in half and see what `collatz-end` gives for that number.  So,
`collatz-end` is defined in terms of itself.  If `n` is an odd number, then we
take triple `n` and add `1`, and see what `collatz-end` gives for that number.

It's not at all obvious that this procedure always evaluates to `1`, but the
smart money says it does.

Recursion
---------
I defined procedure application in terms of parameter rewriting, e.g.
`((λ (x) (+ 3 x)) 9)` means "use `9` instead of `x` in the body of the `λ`",
i.e.  `(+ 3 9)`, which is `12`.

Then what is `define`?

`define` introduces a name (`collatz-end`), and then associates a value with
that name (`(λ (n) (cond ...))`), _where the name is visible inside the
definition of the value._

`define` is a facility provided by the execution environment.  We cannot
get that behavior using `λ`s only.  Or can we?

Consider this anonymous cousin of `collatz-end`:
```scheme
(λ (f)
  (λ (n)
    (cond
      [(= n 1) 1]
      [(even? n) (f (/ n 2))]
      [(odd? n) (f (+ 1 (* 3 n)))])))
```
This is not the same as `collatz-end`.  Instead, it's one "step" in the
execution of `collatz-end`.  Give me a "next" procedure (`f`), and I'll give
you a procedure that takes an `n`, does one Collatz step on it, and then passes
the resulting number to `f`.

Observe how this entire expression is nearly what we want for `f`.

Here's another cousin:
```scheme
(λ (f)
  (λ (n)
    (cond
      [(= n 1) 1]
      [(even? n) ((f f) (/ n 2))]
      [(odd? n) ((f f) (+ 1 (* 3 n)))])))
```
You are forgiven if your head is starting to hurt.  This is like the previous
example, except that now the `f` that we accept is a procedure that takes
a procedure and returns a procedure that takes a nonzero natural number.
That is, `f` is something that looks like the most recent example.

If we apply this procedure to itself, do we get `collatz-end`?
```scheme
((λ (f) (λ (n) (cond [(= n 1) 1] [(even? n) ((f f) (/ n 2))] [(odd? n) ((f f) (+ 1 (* 3 n)))])))
 (λ (f) (λ (n) (cond [(= n 1) 1] [(even? n) ((f f) (/ n 2))] [(odd? n) ((f f) (+ 1 (* 3 n)))]))))
```
This evaluates to a procedure that takes a nonzero natural number, and ...

does the same thing that `collatz-end` does.

Whether an execution environment will demonstrate this fact depends on the
evaluation order used in the execution.  Thanks to the "short-circuit"
evaluation property of `if`, which underlies our `cond`, this procedure really
is the same as `collatz-end`.

Combinators
-----------
The self-applicative monstrosity above is not yet satisfactory, though.  Let's
look at the original procedure again:
```scheme
(define collatz-end
  (λ (n)
    (cond
      [(= n 1) 1]
      [(even? n) (collatz-end (/ n 2))]
      [(odd? n) (collatz-end (+ 1 (* 3 n)))])))
```
This entire snippet of code is the same no matter which name we choose for
`collatz-end`, as long as our choice is not already taken
(`λ`, `cond`, `even?`, ...).

So, `collatz-end` is reasonably thought of as a parameter.  Let's call it `f`.
```scheme
(λ (f)
  (λ (n)
    (cond
      [(= n 1) 1]
      [(even? n) (f (/ n 2))]
      [(odd? n) (f (+ 1 (* 3 n)))])))
```
We're now back to where we were at the beginning of the previous section.  This
procedure is _not_ `collatz-end`, but it's the natural non-recursive analog to
`collatz-end`.  Let's call this procedure `E`.

Can we define a procedure that, given `E`, returns `collatz-end`?

Earlier, we modified `E`, replacing appearances of `f` with `(f f)`.  This
allowed us to describe `collatz-end` as the modified procedure applied to
itself.

It would be nicer if such modification weren't necessary.  Maybe there is a
way to encode that transformation in the operation that takes this anonymous
procedure and gives us `collatz-end`.

Well, we have a procedure that looks like this:
```scheme
(λ (f) (λ (n) ...))
```
where the `...` uses `f` as a procedure taking a natural number, i.e. some
`(λ (n) ...)`.  We want that inner `f` to be based on the overall procedure.

Consider this procedure:
```scheme
(λ (f) (λ (n) ((f f) n)))
```
This is an attempt to encapsulate the transformation we performed in the
previous section; namely, to take a procedure that returns a Collatz-like
procedure, and transform it into a Collatz-like procedure whose inner "next"
procedure is the original procedure applied to itself.

It's hard to say in English.

Let's call this procedure `Sb`, for "antimony."  No, "self-bind."

Then, we can combine `E` and `Sb` to produce an anonymous procedure that might
get us closer to `collatz-end`:
```scheme
(E (Sb E))
```
Remember that `E` is
```scheme
(λ (f)
  (λ (n)
    (cond
      [(= n 1) 1]
      [(even? n) (f (/ n 2))]
      [(odd? n) (f (+ 1 (* 3 n)))])))
```
So, we're looking at (expanding `E` and `Sb`)
```scheme
((λ (f) (λ (n) (cond [(= n 1) 1] [(even? n) ((f f) (/ n 2))] [(odd? n) (f (+ 1 (* 3 n)))])))
 ((λ (f) (λ (n) ((f f) n)))
  (λ (f) (λ (n) (cond [(= n 1) 1] [(even? n) ((f f) (/ n 2))] [(odd? n) (f (+ 1 (* 3 n)))])))))
```
Is this `collatz-end`?

Not quite.  I made a mistake.  Close, but no cigar.  Look at `(E (Sb E))`
again, expanding only `Sb`:
```scheme
(E
  ((λ (f) (λ (n) ((f f) n))) E))
```
That is
```scheme
(E (λ (n) (E E) n))
```
That `λ (n) ...` is passing `E` as the `f` argument to `E`.  But `E` and `f`
have incompatible types!

This construction "`(E (Sb E))`" only works "one layer deep," and then becomes
invalid.

The thing that we pass as the `f` argument to `E` can't be `E` itself, it has
to be the thing we transformed `E` into.

Mind bender!

Alright, let's go back to the thing that works, but is not ideal:
```scheme
(λ (f)
  (λ (n)
    (cond
      [(= n 1) 1]
      [(even? n) ((f f) (/ n 2))]
      [(odd? n) ((f f) (+ 1 (* 3 n)))])))
```
Remember that this thing applied to itself is `collatz-end`.  We need to get
that inner `(f f)` working for us without having it in there.

Here's a transformation to consider:
```scheme
(λ (f) (f f))
```
Well, we want to double up the `f`s and then pass that to `E`, so
```scheme
(λ (f) (E (f f)))
```
Let's expand `E` in that.  Do we get the same thing as "the thing that works,"
above?
```scheme
(λ (f) (E (f f)))
```
```scheme
(λ (f)
  ((λ (f)
     (λ (n)
       (cond
         [(= n 1) 1]
         [(even? n) (f (/ n 2))]
         [(odd? n) (f (+ 1 (* 3 n)))])))
    (f f)))
```
```scheme
(λ (f)
  (λ (n)
    (cond
      [(= n 1) 1]
      [(even? n) ((f f) (/ n 2))]
      [(odd? n) ((f f) (+ 1 (* 3 n)))])))
```
Yes, we do.

Ok, so the operation `(λ (f) (E (f f)))` is the secret sauce.  That gives us
something that we can apply to itself, giving us `collatz-end`.

That is, `collatz-end` is the same as:
```scheme
((λ (f) (E (f f))) (λ (f) (E (f f))))
```
A nicer way to look at it is to consider this operation as a procedure applied
to `E`.  Let's call the procedure `R` for "recursive."
```scheme
(define R
  (λ (E) ((λ (f) (E (f f))) (λ (f) (E (f f))))))
```
Note how now `E` is a parameter.

Then `collatz-end` is the same as
```scheme
(R
  (λ (f)
    (λ (n)
      (cond
        [(= n 1) 1]
        [(even? n) (f (/ n 2))]
        [(odd? n) (f (+ 1 (* 3 n)))]))))
```
A [combinator][8] is a procedure within which every variable has a matching `λ`.

`R` is a combinator.  `E` and `collatz-end` are not, because they depend on the
"free" variables `collatz-end`, `even?`, `=`, etc.

`R` is a particularly famous procedure known as the [Y combinator][9].

Conclusion
----------
Fun stuff, right?  Don't forget to floss your teeth, pay your taxes, take off
your shoes, and be well!

[1]: https://lccn.loc.gov/77011962
[2]: https://en.wikipedia.org/wiki/Lambda_calculus
[3]: https://en.wikipedia.org/wiki/Scheme_(programming_language)
[4]: https://lccn.loc.gov/95039853
[5]: https://en.wikipedia.org/wiki/Natural_number
[6]: https://en.wikipedia.org/wiki/Collatz_conjecture
[7]: http://www.r6rs.org/final/html/r6rs-lib/r6rs-lib-Z-H-13.html#node_sec_12.8
[8]: https://en.wikipedia.org/wiki/Combinatory_logic
[9]: https://en.wikipedia.org/wiki/Fixed-point_combinator#Y_combinator
