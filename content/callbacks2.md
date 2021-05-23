Callbacks (Part 2)
==================
[Previously][part1] I described an API for submitting a query asynchronously
in such a way that the caller provides the object into which the query results
are written, but without having to specify an object factory.  It looked like
this:

    class DatabaseAccessor {

        template <typename Results>
        using Callback = 
            std::function<void(const std::function<void(Results&)>&)>;

        template <typename Results>
        void asyncQuery(const std::string_view&  query,
                        const Callback<Results>& callback);
    };

For brevity, let's define a couple of macros<a id='macros'></a>:


    #define FN(...) std::function<void(__VA_ARGS__)>
    #define CB(...) const FN(__VA_ARGS__)&

So we have:

    class DatabaseAccessor {

        template <typename Results>
        void asyncQuery(const std::string_view&  query,
                        CB(CB(Results&)          callback);
    };

What if, in addition to producing result sets, this database API also has a
concept of output parameters?  These are like query parameters, except that
their values are overwritten by the query rather than used in it.

We could define an overload of `DatabaseAccessor::asyncQuery` that takes a
callback with an amended signature:

    class DatabaseAccessor {

        template <typename Results>
        void asyncQuery(const std::string_view&  query,
                        CB(CB(Results&)          callback);

        template <typename Results, typename OutputParameters>
        void asyncQuery(const std::string_view&            query,
                        CB(CB(Results&, OutputParameters&) callback);
    };

If the user wants output parameters, then he provides a callback that fits
the second signature, while if he doesn't want output parameters, he specifies
a callback that fits the first signature.

Injecting a Default
-------------------
Most users don't want output parameters.  They're a strange concept in
databases, they can always be replaced by multiple result sets instead, and
Microsoft SQL Server is the only database I've worked with that has them.  It
would be ideal to appropriate as little code in our library to support them as
possible.

To this end, observe that since this library deduces the structure of its
output from the types of the output parameters (using [this][bdlat]), to omit
the `OutputParameters` argument is the same as if you specified one, but one
whose structure describes the absence of data: an "empty sequence."

In other words, if you don't specify the `OutputParameters`, the library knows
to expect no output parameters from the query.  Also, though, if you specify
an `OutputParameters` that has no members, the library knows to expect no
output parameters.

So, let's define a helper type, `EmptySequence`, that has no members and
introspection into which indicates "nothing to put here."  Then the first
overload of `DatabaseAccessor::asyncQuery` can be written in terms of the
second, "as if" the user had specified an `EmptySequence` for
`OutputParameters` rather than not specifying that argument at all.

How do you write this?  I find it very tricky to think about.

Writing the Forwarding Implementation
-------------------------------------
Let's look at the code again:

    class DatabaseAccessor {

        template <typename Results>
        void asyncQuery(const std::string_view&  query,
                        CB(CB(Results&)          callback);

        template <typename Results, typename OutputParameters>
        void asyncQuery(const std::string_view&            query,
                        CB(CB(Results&, OutputParameters&) callback);
    };

We want to implement the first in terms of the second using the `EmptySequence`
type for the dummy `OutputParameters`.

    template <typename Results>
    void DatabaseAccessor::asyncQuery(const std::string_view& query,
                                      CB(CB(Results&)         callback)
    {
        asyncQuery(query, /* ? */);
    }

The difference, of course, is in the second argument of each `asyncQuery`
overload.  We're given a function that takes a function that takes a
`Results&`, and we need to call the overload that takes a function that takes
a function that takes a `Results&` and an `EmptySequence&`, and we must
additionally see to it that the `EmptySequence&` refers to some (dummy)
instance.

One way to think about this is that we need a function, `injectDummy`, that
maps one type of function into another type of function:

    template <typename Results>
    void DatabaseAccessor::asyncQuery(const std::string_view& query,
                                      CB(CB(Results&)         callback)
    {
        asyncQuery(query, injectDummy(callback));
    }

where `injectDummy` has the following signature:

    template <typename Results>
    FN(CB(Results&, EmptySequence&)) injectDummy(CB(CB(Results&)));

You might want to look again at what the `FN` and `CB` [macros](#macros) mean.

You know that thing where when you have a cube drawn in two dimensions, you can
think of some of its corners as popping out of the page at you _or_ as going
into the page, and if you do something weird in your mind you can switch back
and forth?

I feel like figuring out an answer to this C++ puzzle gave me a new sort of
facility along those lines.  Here's the implementation of `injectDummy` that I
came up with, written using lambda expressions:

    template <typename Results>
    FN(CB(Results&, EmptySequence&)) injectDummy(CB(CB(Results&)) callback)
    {
        return [=](CB(Results&, EmptySequence&) innerCallback) {
            EmptySequence dummy;
            callback([&](Results& results) {
                innerCallback(results, dummy);
            });
        };
    }

It's not complicated at all once it's written down.

I don't know enough Haskell to say whether there's a fancy name for this
operation, but it does feel a bit mathy, doesn't it?

So there we have it -- the no-output-parameters overload written in terms of 
the output-parameters overload:

    template <typename Results>
    FN(CB(Results&, EmptySequence&)) injectDummy(CB(CB(Results&)) callback)
    {
        return [=](CB(Results&, EmptySequence&) innerCallback) {
            EmptySequence dummy;
            callback([&](Results& results) {
                innerCallback(results, dummy);
            });
        };
    }

    template <typename Results>
    void DatabaseAccessor::asyncQuery(const std::string_view& query,
                                      CB(CB(Results&)         callback)
    {
        asyncQuery(query, injectDummy(callback));
    }

A colleague of mine called this "like the opposite of bind," or maybe it's an
inside-out bind.  Six lines of C++11 is what it is.

[part1]: callbacks.html
[bdlat]: https://bloomberg.github.io/bde/group__bdlat.html
