Go Shoot Yourself in the Foot
=============================
![gopher with a gun](gopher-gun.webp)

What's the output of the following program?
```go
package main

import (
	"fmt"
)

func foo() (result string) {
	defer func () { fmt.Printf("foo result = %q\n", result) }()
	return "hi"
}

func bar() (result string) {
	defer fmt.Printf("bar result = %q\n", result)
	return "hi"
}

func main() {
	fmt.Printf("foo() = %q\n", foo())
	fmt.Printf("bar() = %q\n", bar())
}
```
First `foo` is executed, which will print something, and then the first line of
`main` will print something.

Then `bar` is executed, which will print something, and then the second line
of `main` will print something.

Here's the output:
```text
foo result = "hi"
foo() = "hi"
bar result = ""
bar() = "hi"
```
Does the third line surprise you?  It sure surprised me.  Go ahead, [try it][1] yourself.

Why
---
Reading StackOverflow [didn't help][2].  Instead, I had to read the
[language specification][3], which is what I ought always to do.

> Each time a "defer" statement executes, the function value and parameters to
> the call are evaluated as usual and saved anew but the actual function is not invoked.

The parameters are evaluated when the _defer statement_ executes, not when the
deferred function is invoked.

This is confusing, because one way to defer code is to wrap it in a closure
(`func`) and invoke the closure later on.

Go's `defer` statement is more general.  After thinking about it, I prefer the
Go way, except that now I have this hole in my foot.

Be careful out there.

[1]: https://play.golang.org/p/8NyKwSbRS_c
[2]: https://stackoverflow.com/a/37249043
[3]: https://golang.org/ref/spec#Defer_statements
