The Thrush Combinator
=====================

```javascript
const thrush = (value, func, ...funcs) =>
    func ? thrush(func(value), ...funcs) : value;
```

I was looking up how I've [previously][1] used [requirejs][2] and noticed the
function definition above.

Some call this the [thrush combinator][3], though I don't know if it's really
a thing.  It has nothing to do with [HIV][8].

The idea is that you have an initial value on which you want to perform a
sequence of transformations.  For example, in a UNIX shell, you might write

```console
$ echo foobar | tr i x | sed 's/./\0\n/g' | sort | uniq -c | sort -rn | head -1
      2 o
```

In programming languages with function invocation syntax, you might write

```javascript
const result = finally_this(and_then_this(then_this(do_this(initial_data))))
```

The order in which those functions are applied reads right-to-left:

1. You start with `initial_data`,
2. then you apply `do_this` to `initial_data`,
3. then you apply `then_this` to the result of (2),
4. then you apply `and_then_this` to the result of (3),
5. then you apply `finally_this` to the result of (4),
6. and then (5) is the answer.

`thrush` allows you to rewrite that expression in the following way:

```javascript
const result =
    thrush(initial_data, do_this, then_this, and_then_this, finally_this);
```

That looks more like the shell pipeline.  It also looks like a sequence of
statements in an imperative programming language, where there is an implicit
[sequence point][4] after each function invocation:

    declare initial_data;
    do_this();
    then_this();
    and_then_this();
    finally_this();

In programming languages with objects and methods, this is sometimes expressed
as a chain of method invocations and called a [fluent interface][5]:

```javascript
const result =
    initial_data.do_this().then_this().and_then_this().finally_this();
```

That's often formatted vertically to give an imperative feel:

```javascript
const result =
    initialdata
    .do_this()
    .then_this()
    .and_then_this()
    .finally_this();
```

Clojure has a macro version of the thrush combinator, spelled [->][5], and
confusingly called the "threading macro":

```clojure
(def result
  (-> initial-data do-this then-this and-then-this finally-this))
```

Getting back to the Javascript implementation from before:

```javascript
const thrush = (value, func, ...funcs) =>
    func ? thrush(func(value), ...funcs) : value;
```

Isn't it cool how that works?  Maybe it's clearer with less syntax, in
[Racket][7]:

```scheme
(define (thrush value . funcs)
  (if (empty? funcs)
    value
    (apply thrush (cons ((first funcs) value) (rest funcs)))))
```

Yuck, that didn't help at all.  Maybe pattern matching will help.  How about
this?

```scheme
(define thrush
  (match-lambda*
    [(list value) value]
    [(list value func funcs ...) (thrush (func value) funcs ...)]))
```

Getting better?  Maybe it's clearer as a pattern matching _macro_ instead of as
a function:

```scheme
(define-syntax thrush
  (syntax-rules ()
    [(thrush value) value]
    [(thrush value func funcs ...) (thrush (func value) funcs ...)]))
```

They're really very similar, aren't they?

This makes me wonder what a horrid affair this would be in C++.  Let's try it:

```c++
#include <utility>

template <typename Value>
Value&& thrush(Value&& value) {
    return std::forward<Value>(value);
}

template <typename Value, typename Func, typename ... Funcs>
auto thrush(Value&& value, Func&& func, Funcs&&... funcs) {
    return thrush(func(std::forward<Value>(value)),
                  std::forward<Funcs>(funcs)...);
}
```

The `auto` function with a deduced return type (i.e. without a trailing return
type) is a C++14 feature.  You know, if it weren't for the `std::forward`
noise, this would be nearly as clean as the Racket code.  Maybe we can omit the
`std::forward` calls and it will only matter sometimes.  What do I know?  Let's
see what that looks like:

```c++
#include <utility>

template <typename Value>
Value thrush(Value&& value) {
    return value;
}

template <typename Value, typename Func, typename ... Funcs>
auto thrush(Value&& value, Func&& func, Funcs&&... funcs) {
    return thrush(func(value), funcs...);
}
```

Hot damn!  What about using `class` instead of `typename`?

```c++
#include <utility>

template <class Value>
Value thrush(Value&& value) {
    return value;
}

template <class Value, class Func, class ... Funcs>
auto thrush(Value&& value, Func&& func, Funcs&&... funcs) {
    return thrush(func(value), funcs...);
}
```

That's pretty good.  The last thing I'd do is make the first overload `auto`,
even though it doesn't save us much.  It makes the two overloads more
consistent:

```c++
#include <utility>

template <class Value>
auto thrush(Value&& value) {
    return value;
}

template <class Value, class Func, class ... Funcs>
auto thrush(Value&& value, Func&& func, Funcs&&... funcs) {
    return thrush(func(value), funcs...);
}
```

Not too shabby.  Still can't beat Javascript, though.

```javascript
const thrush = (value, func, ...funcs) =>
    func ? thrush(func(value), ...funcs) : value;
```

What about in [Go][9]?  Forget it.

[1]: https://github.com/dgoffredo/llama/blob/master/bin/llama.js
[2]: https://requirejs.org/
[3]: https://www.google.com/search?q=thrush+combinator
[4]: https://en.wikipedia.org/wiki/Sequence_point
[5]: https://en.wikipedia.org/wiki/Fluent_interface
[6]: https://clojuredocs.org/clojure.core/-%3E
[7]: https://racket-lang.org/
[8]: https://en.wikipedia.org/wiki/Linear_gingival_erythema
[9]: https://golang.org/
