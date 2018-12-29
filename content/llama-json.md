Llama JSON
==========
Playing with a [pet project][pet project], I noticed a relationship between
[s-expressions][s-expressions] and [JSON][JSON].

The following JSON is also valid [Llama][pet project]:

    {
        "hello": null, 
        "isn't": ["it", 2, "conveninent?"]
    }

Since 

- `{`, `[`, and `(` are intechangable in Llama (though they must match up),
- the comma (`,`) is considered whitespace, and
- the colon (`:`) and `null` are valid symbol names,

the above is the same as:

    ("hello" ': 'null "isn't" ': ("it" 2 "convenient?"))

Does that mean we can represent JSON text within Llama without having to escape
our quotes?

    (Document ((version 1.1) (xmlns "http://mycompany.com"))
      (Widget ((name Fred))
        (_.content
          (json {
              "columns": ["Foo", "Bar", "Baz"],
              "rows": [
                  [1, 2, 3],
                  [null, null, null]
              ]
          }))))

Ideally that would be the same as:

    (Document ((version 1.1) (xmlns "http://mycompany.com"))
      (Widget ((name Fred))
        (_.content
          "{
              \"columns\": [\"Foo\", \"Bar\", \"Baz\"],
              \"rows\": [
                  [1, 2, 3],
                  [null, null, null]
              ]
          }")))

Values could even be substituted in:

    (let ([names ("John" "Paul" "George" "Ringo")])
      (json {
          "Beatles": names,
          "musicians": names,
          "Brits": names
      }))

yielding:

    "{
         \"Beatles\": [\"John\", \"Paul\", \"George\", \"Ringo\"],
         \"musicians\": [\"John\", \"Paul\", \"George\", \"Ringo\"],
         \"Brits\": [\"John\", \"Paul\", \"George\", \"Ringo\"]
    }"

Perhaps even [computed property names][computed property names]:

    (let ([key "Willy Wonka"])
      (json {[key]: "value"}))

It's a happy coincidence that the syntax for computed property names looks like
a Llama list. The above expands to:

    (json (("Willy Wonka") ': "value"))

It's not hard to imagine that the `json` form might have a special case for
lists in property name position -- just pretend the (singular) contents of
the list were there instead.

The one thing that bothers me is Javascript-style unquoted property names:

    {
        "quoted": "value",
        unquoted: "value"
    }

In Javascript (but notably _not_ in JSON), that's the same as if the second
property name were in quotes:

    {
        "quoted": "value",
        "unquoted": "value"
    }

In particular, in Javascript, even if there's a variable named `unquoted`, that
property name is literally `"unquoted"`, not the value of `unquoted`; hence
the special syntax for computed property names.

The `unquoted:` case is a challenge for our `json` feature, because
`unquoted:` is a single Llama token, and it's a valid symbol. It just
happens to end with the colon character. I could forbid this case to make
things easier, but why not support it? Llama is all about finding the sweet
spot between brevity and readability.

And what will `json` be, exactly, in Llama? Is it a procedure? A macro? A
special intrinsic?

I work through these and other questions in the following sections, and then
propose a definition for the `json` form.

It's a Macro
------------
Well, there you have it. It has to be a macro, not a regular procedure. Here's
why:

    (let ([: "colon lol"])
      (json {"foo": "bar"}))

As perverse as that might seem, it's perfectly valid to bind the symbol named
`:` to some value. If `json` were a normal procedure, its arguments would be
evaluated first, and so the list of arguments going into `json` would end up
being `("foo" "colon lol" "bar")`, and we just can't have that. With a macro,
though, whatever literally appears as the argument is what is passed in, e.g.
the symbol `:`.

We're not out of the woods yet, though.

Dealing with `null`
-------------------
`null` is a special symbol that has to be dealt with. The trouble is that
the symbol `null` might be bound to some value during evaluation. I think,
therefore, it's best to force `null` always to mean `null` within a `json`
form. However, it's reasonable to accept it as a valid value after
evaluation as well, so that this:

    (let ([nada null])
      (json {value: nada}))

yields

    "{\"value\": null}"

As an aside, note that the appearance of `null` in the `let` binding, above,
would need to be `'null` (quoted) if `null` were bound to a value above. That
is, while the expression above is fine, the following:

    (let ([null "oops!"]
          [nada null])
      (json {value: nada}))

would yield a different answer; namely,

    "{\"value\": \"oops!\"}"

In order to refer to the literal `null`, it has to be prefixed by the quoting
character:

    (let ([null "oops!"]
          [nada 'null])
      (json {value: nada}))

so that once again the result is `"{\"value\": null}"`.

So, `null` will be treated literally without evaluation when appearing in a
`json` form, but the value after evaluation will also be accepted.

Distinguishing Arrays from Objects
----------------------------------
Trickier even than encountering the colon (`:`) symbol are the situations we
get into supporting `unquoted:` property names. Is the following a JSON
object, or JSON array having two elements?

    (foo: "bar")

Well, we have to decide. Fortunately, JSON does not have a concept of
"symbols" [like][edn] most [s-expressions][s-expressions] do, and so we can
forbid them outright in the final output of the `json` form (except for
`null`).

This means that the example above, `(foo: "bar")` is a JSON object with one
property named `"foo"` having the value `"bar"`.

Or is it? What if `foo:` were a name bound to some other value?

    (let ([foo: "gotcha"])
      (json (foo: "bar")))

Now we might want this to expand to `(json ("gotcha" "bar"))`, and that looks
at lot more like a JSON array having two elements, i.e. `["gotcha", "bar"]`.

What are we going to do? If the symbol `foo:` is bound to some value, and we
encounter `foo:` within a `json` form in a context where it could decide the
object-ness of a form, did the programmer intend for it to be the unquoted
property named `"foo"`, or did they intend for an array element having the value
bound to the name `foo:`?

It's once again tempting to disallow unqouted property names, as in JSON; but
then it seems awkward having the `{[computed]: "property names"}` borrowed from
Javascript without also having the unquoted property names.

One idea that helps is to parse symbols-ending-in-colon as unquoted property
names, _during macro expansion_, before any potential value substitution. This
means that

    (let ([tricky: "look out!"])
      (json {tricky: "tricks"}))

yields `"{\"tricky\": \"tricks\"}"` instead of `"[\"look out!\" \"tricks\"]"`.
That settles that ambiguity, but still we have a problem if the object or array
is _empty_.

Empty Objects and Arrays
------------------------
What does `(json ())` yield? Is it `"[]"` or is it `"{}"`? Remember that the
different types of grouping characters are indistinguishable in Llama.

This presents a serious problem -- it reveals that in order to _truly_ represent
JSON unambiguously in Llama, we'd need the help of the reader (the parser). The
reader knows, after all, which of `(`, `{`, or `[` it encountered, because it
must match it up with the corresponding `)`, `}`, or `]`.

I'm tempted to add this information to the output of the parser. Right now, a
datum is represented in the implementation as a Javascript object whose sole
property name tells you the type and the value at that propery is the value,
e.g.

    const listOfNumbers = {list: [{number: "1"}, {number: "2"}, {number: "3"}]},
          aNumber       = {number: "13"},
          aString       = {string: "hello"};

The datum `listOfNumbers` could have been parsed from any of `(1 2 3)`,
`[1 2 3]`, or `{1 2 3}`, but the parser has jettisoned the distinction.

What if a list datum had an additional property, "suffix"?

    const listOfNumbers = {list: [{number: "1"}, {number: "2"}, {number: "3"}],
                           suffix: "]"};

This way, we would know that it was `[1 2 3]` to begin with.

Doing this would solve the "empty object or array?" problem, at the cost of
requiring that the `json` form be implemented as an intrinsic macro --
macros and procedures written in Llama would not have access to this extra
information found in the implementation. Instead, the macro would have to be
written in Javascript.

I see no way around it. The parser has to be modified to preserve the
distinction among the various flavors of lists. Doing this will require some
subtle changes "downstream," as well, since we have to make sure that we
don't accidentally consider a list's "suffix" as part of its value. That is,
I still want `(1 2 3)`, `[1 2 3]`, and `{1 2 3}` to be considered equal, except
in contexts where the distinction is explicitly relevant, like in the `json`
macro.

That work was done in [this commit][suffix-commit]. In doing so, I accidentally
introduced a bug, which I fixed in [the following commit][matching-commit].

Numbers and `JSON.stringify`
----------------------------
There's one more sticky point, before we get into the implementation. When
first thinking about the implementation, I thought it would be convenient to
have the `json` form produce a _javascript_ value suitable for JSON
serialization by `JSON.stringify`, so that all I have to do is "unpack" the
AST nodes into a form that `JSON.stringify` understands, and then it would
do the serialization for me.

This would work fine, except that the only way to get `JSON.stringify` to
print a number is to give it a Javascript `Number`. Javascript numbers,
though, are [always][es6-numbers] stored in [IEEE double precision floating
point format][double].

So what? Double precision floating point is good enough for everybody, right?

No! We must support arbitrary numbers, as defined in the Llama
[grammar][llama-grammar]! (Or, for that matter, the [JSON grammar][json-number])

In order to do this, the textual content of Llama numbers has to be bypassed
through the JSON serializer, and since `JSON.stringify` does not support this
(even with its `replacer` argument!), we have to do our own JSON serialization.

Fortunately, JSON is simple, and also we can still use `JSON.stringify` for
`String`s, `null`, `Date`s, and any other non-numeric scalars.

Helper Procedure
----------------
Before we get into writing the `json` macro itself, recognize that the job
of converting an evaluated list of data (datums) into a string of JSON can
be done by a procedure, once the colon business has been taken care of, and
so the job of the `json` macro will be to take care of the colon business
and then produce an invocation of this procedure.

The input to the helper procedure will be a Llama datum that has received the
following pre-processing by the macro:

- Colon (`:`) symbols have been removed from lists that denote objects (lists
  ending with `"}"`).
- Unquoted property names (e.g. `foo:`) will have been replaced with strings
  lacking the trailing colon (e.g. `"foo"`) in lists that denote objects.
- Instances of the symbol `null` will have been quoted (in the lisp sense), so
  that `null` means `null` regardless of whether the symbol is bound to a value.

So, the job of the helper procedure is to convert, for example, the following
Llama (note the lack of colons):

    [1, {"foo" "hi" "bar" null}]

whose AST is the following Javascript object:

    {
        suffix: ']',
        list: [
            {number: '1'},
            {
                suffix: '}',
                list: [
                    {string: 'foo'},
                    {string: 'hi'},
                    {string: 'bar'},
                    {symbol: 'null'}
                ]
            }
        ]
    }

into the following Javascript object:

    [
        {[numberProperty]: '1'},
        {
            foo: 'hi',
            'bar': null
        }
    ]

where `numberProperty` is a special string recognized by the JSON serializer to
mean the contained string is to be serialized as a number rather than as a
(quoted) string. You can see what I mean [in the code][number-property].

The helper procedure is called [jsonify][jsonify-function] in the
implementation. The only hairy part was walking through a list [two elements
at a time][two-at-a-time] (Javascript's "splat" (`...`) operator and
recursion helped here).

The `json` Macro
----------------
All that remains to write is the `json` macro itself, which will prepare its
argument for the helper procedure and then expand into an invocation of the
helper procedure with the modified argument, i.e.

    (json argument)

becomes

    ((lambda ...) modified-argument)

so that then the evaluator will evaluate `modified-argument` before applying it
to the helper procedure.

The macro-time massaging of the argument happens in the
[removeColonsFromObjects][colons] function, which also does the `null` quoting
(I need to change the name to indicate that...).

After the massaging, the macro expands to an [invocation
expression][invocation-expression], and finally the helper procedure does
its work before calling the [custom JSON serializer][json-serializer].

With that, we're done! JSON embedded within a lisp, using macros.

Example
-------
Input (Llama):

    (pml ((xmlns http://www.proprietary.com/ui)
          (xmlns:pml http://www.proprietary.com/markup))
      (Table ((pml:name tickets))
        (_.dataSource
          (pml:json (json
            (let ([(row ticket status owner desc)
                   {ticket: ticket, status: status, owner: owner, desc: desc}])
            {
                columnTitles: ["Ticket", "Status", "Owner", "Description"],
                rows: [
                    (row 11333 "open"   "Bob"   "The darn thing doesn't work")
                    (row 11334 "closed" "Bob"   "Could you do this for me?")
                    (row 11332 "open"   "Alice" "URGENT: label is wrong color")
                ]
            }))))))

Output (XML, after additional formatting):

    <pml xmlns="http://www.proprietary.com/ui"
         xmlns:pml="http://www.proprietary.com/markup">
      <Table pml:name="tickets">
        <_.dataSource>
          <pml:json>{
              "columnTitles": ["Ticket", "Status", "Owner", "Description"],
              "rows": [
                  {
                      "ticket": 11333,
                      "status": "open",
                      "owner":  "Bob",
                      "desc":   "The darn thing doesn't work"
                  },
                  {
                      "ticket": 11334,
                      "status": "closed",
                      "owner":"Bob",
                      "desc": "Could you do this for me?"
                  },
                  {
                      "ticket": 11332,
                      "status": "open",
                      "owner":"Alice",
                      "desc": "URGENT: label is wrong color"
                  }
              ]
          }</pml:json>
        </_.dataSource>
      </Table>
    </pml>

You can try it out by cloning [Llama][pet project] onto your computer and
opening the [playground][playground] in a web browser.

[pet project]: https://github.com/dgoffredo/llama
[s-expressions]: https://en.wikipedia.org/wiki/S-expression
[JSON]: https://en.wikipedia.org/wiki/JSON
[computed property names]: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Object_initializer#Computed_property_names
[edn]: https://github.com/edn-format/edn
[suffix-commit]: https://github.com/dgoffredo/llama/commit/66197fa9774b1f3cbf17a5e76c6a81df44cce5d1
[matching-commit]: https://github.com/dgoffredo/llama/commit/6ccf8a1b1c10909f8295ea906c1acc96e421031f
[double]: https://en.wikipedia.org/wiki/Double-precision_floating-point_format
[es6-numbers]: http://www.ecma-international.org/ecma-262/6.0/#sec-terms-and-definitions-number-value
[llama-grammar]: https://github.com/dgoffredo/llama#grammar
[json-number]: https://tools.ietf.org/html/rfc7159#section-6
[number-property]: https://github.com/dgoffredo/llama/commit/f8c833f7fdc685385d2ae6b6bfb51cf2f4b61cac?diff=unified#diff-245ec6b1bfcfd67da8e9e5c842ac921bR69
[jsonify-function]: https://github.com/dgoffredo/llama/commit/f8c833f7fdc685385d2ae6b6bfb51cf2f4b61cac?diff=unified#diff-245ec6b1bfcfd67da8e9e5c842ac921bR80
[two-at-a-time]: https://github.com/dgoffredo/llama/commit/f8c833f7fdc685385d2ae6b6bfb51cf2f4b61cac?diff=unified#diff-245ec6b1bfcfd67da8e9e5c842ac921bR44
[colons]: https://github.com/dgoffredo/llama/commit/f8c833f7fdc685385d2ae6b6bfb51cf2f4b61cac?diff=unified#diff-245ec6b1bfcfd67da8e9e5c842ac921bR194
[invocation-expression]: https://github.com/dgoffredo/llama/commit/f8c833f7fdc685385d2ae6b6bfb51cf2f4b61cac?diff=unified#diff-245ec6b1bfcfd67da8e9e5c842ac921bR271
[json-serializer]: https://github.com/dgoffredo/llama/commit/f8c833f7fdc685385d2ae6b6bfb51cf2f4b61cac?diff=unified#diff-245ec6b1bfcfd67da8e9e5c842ac921bR127
[playground]: https://github.com/dgoffredo/llama#using-the-playground