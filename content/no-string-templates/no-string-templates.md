Don't Use String Templates for Structured Output
================================================
`<html>{{foo}}</html>` ❌

`['html', foo]` ✅

Temptation
----------
You're writing a web server that does server side rendering of HTML for a
website. Pages are mostly static, but they differ slightly from session to
session.

I know, I'll write a `page.template.html` that looks like HTML but contains
`{{special syntax}}` or maybe `<%special syntax%>`. Then my web server will
read the file, replace the special syntax sections with markup based on logic
of my choosing, and then serve the resulting string as HTML.

You're writing a [Kubernetes controller][1], and you know that the resources
managed by the controller will need their own YAML configurations, but the YAML
will have to differ based on the configuration of the controller.

I know, I'll write a `deployment.yaml` file that isn't actually YAML, but
instead is a mix of YAML and Go's [text template][2] syntax. I'm using Go
already, so I can just `tmpl.Execute(output, myData)`, and voila,
`myData.Thingy` is now part of the YAML where there was once `{{.Thingy}}`.

You're writing a code generator to automate the more tedious parts of a
programmatic interface.  Maybe the generated code contains message types for
use with an RPC framework in a statically typed language.  Maybe the generated
code marshals the results of known SQL statements into a library's types. Maybe
the generated code encodes a set of types into some serialization format like
JSON or Protocol Buffers.

I know, using string templates naively could get out of hand here since we're
working with a general purpose programming language. I'll just write escaping
functions to make sure that `"` is escaped when inside of a double-quoted
string, and I'll write validation functions to make sure that the name of a
variable doesn't include a comment opening sequence (`/*`).

I can use string templates to generate everything, so long as I'm careful.

Abstinence
----------
Stop doing this. If your goal is to end up with a string containing language X,
then you cannot begin with a string.  Instead, you must begin with a
representation of language X. Then, perform any desired transformations _within
the representation of language X_, and only at the very end render the
representation into a string.

It's not overkill. The problem of altering structured data is _different_ from
the problem of manipulating strings.  Don't use the latter just because it's on
hand or because the alterations seem trivial.  Find a library that allows you
to represent the target language in your programming language of choice, or
otherwise write your own.

Once your project is a soup of string templates supporting an increasingly
complex mini-language of syntax oblivious interpolation operations, _it's too
late to replace it with something better._  You must _start_ with a
representation of the target language.

You don't necessarily need to have a representation that covers the entire
language — it need only cover what you will generate.  Add bells and whistles
later as needed.

My Examples
-----------
- Okra, a limited object relational mapper, contains a representation of a
  subset of Go ([schema][3], [example usage][4]).
- My blog generates an Atom feed by using Python `list`s and `dict`s to
  [represent XML][5].
- [namedsql][11] is a Go library that extends the SQL dialect supported by the
  Go standard library by first [lexing][6] SQL into a token representation and
  then [rendering][7] the result at the end.
- [sqlbindarray][8] is a Python module that does a similar thing.
- Llama, a configuration language that compiles to XML, contains its own
  [representation of XML][9] that is [rendered][10] to a string just before
  output.


[1]: https://kubernetes.io/docs/concepts/architecture/controller/
[2]: https://pkg.go.dev/text/template
[3]: https://github.com/dgoffredo/okra/blob/master/crud-languages/go/ast.tisch.js
[4]: https://github.com/dgoffredo/okra/blob/fdf25d1f34c3f761425b6c257578d312fbf7b0ca/crud-languages/go/generate.js#L629-L642
[5]: https://github.com/dgoffredo/dgoffredo.github.io/blob/master/bin/sxml.py
[6]: https://github.com/dgoffredo/namedsql/blob/master/namedsql/lexer.go
[7]: https://github.com/dgoffredo/namedsql/blob/9dae02f56e0fbf724dc53e545a34b8ea30265e6b/namedsql/lexer.go#L165-L174
[8]: https://github.com/dgoffredo/sqlbindarray
[9]: https://github.com/dgoffredo/llama/blob/master/llama/xml.js
[10]: https://github.com/dgoffredo/llama/blob/cc92b1618cbe1aa74336671606d7a03e1b2e6099/llama/xml.js#L214-L234
[11]: https://github.com/dgoffredo/namedsql
