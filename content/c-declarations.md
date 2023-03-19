C Declarations
==============
In C, C++, and Java, why do variable declarations put the primitive type name
on the left and not on the right?  Declaring a variable `x` of type `int` is
this:
```C
int x;
```
instead of this:
```C
x int;
```
Don't get distracted!  You were about to explain how in C, declaration syntax
is analogous to expression syntax, weren't you?  You were about to tell me
about [cdecl][1] and how [Go did it differently][2] after years of programmers
complaining about the C syntax.  You were going to offer an opinion too,
weren't you?

That's not what I'm talking about.  The fact that `int x;` means

> Declare `x` such that the expression "`x`" has type `int`.

and that `int (**x)(double, char)[2];` means

> Declare `x` such that the expression "`(**x)(d, c)[i]`" has type `int` for
> given `double d`, `char c`, and `int i`.

does not explain why the `int` is there on the left.  It could be on the right.
Could it?

I mentioned this in a [Hacker News comment thread][3], and someone replied:

> Because parsers, like humans, read from left to right. Important parsing
> decisions are usually made as early as possible. An example is recursive
> descent parsing, which derives its simplicity from making decisions first,
> allowing a top-down parse. And when humans skim text, I bet it can be shown
> that it's easier if the syntactically significant locations are aligned near
> the beginning of each statement.

The idea is that a C compiler reads input from left to right, and that knowing
that the ultimate primitive type asserted by the declaration is `int` is useful
to know at the beginning of parsing the declaration, as opposed to at the end.

Maybe this was important in 1972, but I don't think it is today.  On the other
hand, I've never written a C parser.  Maybe the presence of a type name (`int`)
at the beginning of the parse lets us know that we're parsing a type
declaration, and not some expression. Maybe that's helpful for avoiding
ambiguity.

When in doubt, ask ChatGPT.  Given the following prompt:

> In the C programming language, why does the primitive type name appear on the
> left in a declaration, and not on the right?
> 
> For example, the following code declares a variable "x" with type "int":
> 
>     int x;
> 
> Why is it not instead:
> 
>     x int;
> 
> Why might this design have been chosen?

ChatGPT generated:

> The C language's syntax for declaring variables with a type name on the left
> and the variable name on the right was influenced by earlier languages such
> as B and BCPL. This syntax was chosen for a few reasons:
>
> - Readability: Placing the type name first makes it easy to quickly identify
>   the type of a variable when scanning code.
> - Parsing: The type name first makes it easier for compilers to parse
>   declarations. The compiler can look for a specific pattern (type name
>   followed by variable name) when parsing declarations, which simplifies the
>   process.
> - Consistency: Placing the type name first makes declarations more consistent
>   with function definitions, where the return type is also placed first.
>
> In general, the C language was designed to be simple and straightforward, and
> the syntax for variable declarations is no exception. The current syntax has
> become a standard convention and is widely used in many other programming
> languages as well.

It claims we have to look further back than C to the languages on which it's
based.  Fair enough.

The "readability" point I'll ignore, since what is readability anyway?

The "parsing" point is the same one made by the Hacker News commenter, so
maybe there's something to that.

The final point, "consistency," is interesting.  The idea is that since
function declarations have their return type on the left, that variable
declarations should follow suit for consistency.

I don't buy this point, because function declarations are declarations.  Unless
there's some historical explanation where function declaration syntax existed
before variable declaration syntax (plausible in a world where all variables
are machine words), then there's still the question of "why is the return type
on the left?" which is then the same question as "why is the ultimate primitive
type on the left?"

After asking one human and one bot, the reason is still a mystery to me.  Maybe
the answer is just "because that's the syntax they chose."

[1]: https://cdecl.org/
[2]: https://go.dev/ref/spec#Variable_declarations
[3]: https://news.ycombinator.com/item?id=35217860#35222262
