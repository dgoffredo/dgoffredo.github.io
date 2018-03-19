Callbacks (Part 1)
==================
I ran into something cool related to callbacks lately, and I have to tell you
about it.

User-Specified Types
--------------------
Say you're writing an API for some sort of query or RPC system.  Maybe you're
writing a client library for a request/response message passing framework, or
maybe you're writing a database accessor.

Also suppose that there's [some system][bdlat] of compile-time introspection
that you and your users have agreed upon, so that they can indicate the
structure of their data in the types of object that they use with your API.

This means that one way to write your API is using templates.  For example:

    class DatabaseAccessor {

        template <typename Results, typename Parameters>
        void syncQuery(const std::string_view& query,
                       Results&                results,
                       const Parameters&       parameters);
    };

The user specifies a (SQL?) query, a reference to an object into which the
results can be written, and a reference to an object from which the query
parameters (if any) can be read.

`DatabaseAccessor::syncQuery` will submit the query to the database, and then
when results are received, it will deduce how to unpack them into `results` by
using the [introspection facilities](bdlat) associated with the type `Results`.
Pretty cool.

Runtime Object Structure
------------------------
The above recipe works even if the structure of `Results` is not certain at
compile time.  It could be that when a `Results` object is created, it takes
as one of its constructor arguments a "schema" object that determines how the
object will behave at runtime, e.g. "pretend to be an array of strings," or
"pretend to be a choice between a string named 'foo' and a pair of integers
named 'bar'."

The reason that it works is that in this synchronous API, the user creates the
`Results` object, not the library:

    DynamicValue      results(parseSchema("fpml_exotics.xsd"), "Stellar");
    StellarParameters params = /* ... */;

    database.syncQuery("execute GetContract(@id, @client);", results, params);

_But what about an asynchronous API?_  In that case, it's the library that will
be creating the `Results` object.  For example:

    class DatabaseAccessor {

        template <typename Results>
        using Callback = std::function<void(Results&)>;

        template <typename Results, typename Parameters>
        void asyncQuery(const std::string_view&  query,
                        const Callback<Results>& callback,
                        const Parameters&        parameters);
    };

The user provides a function that takes a `Results`, but where does that
`Results` object come from?  It's created by the library:

    void onResponse(DynamicValue& results) {
       // ...
    }

    database.asyncQuery("execute GetContract(@id, @client);",
                        std::function<void(DynamicValue&)>(&onResponse), 
                        params);

What happened to the stuff about the schema?  This is trouble, because unlike
with a type whose structure is known at compile-time, the library can't just
default construct an object and fill it up using introspection, and unlike in
the synchronous API, the library can't have the user provide the object.

Or can it?

Factories
---------
One way to get around this shortcoming is to have a version of the asynchronous
API that takes an additional "factory" argument from which objects of the
`Results` type can be constructed.  This way, the user can specify any dynamic
construction logic in the factory.  It might look like this:

    class DatabaseAccessor {

        template <typename Results>
        using Callback = std::function<void(Results&)>;

        template <typename Results>
        using Factory = std::function<Results()>;

        template <typename Results, typename Parameters>
        void asyncQuery(const std::string_view&  query,
                        const Callback<Results>& callback,
                        const Parameters&        parameters,
                        const Factory<Results>&  resultsFactory);
    };

This solves the conundrum.  Now the user can write this:

    DynamicValue makeStellar() {
        return DynamicValue(parseSchema("fpml_exotics.xsd"), "Stellar");
    }

    void onResponse(DynamicValue& results) {
       // ...
    }

    database.asyncQuery("execute GetContract(@id, @client);",
                        std::function<void(DynamicValue&)>(&onResponse), 
                        params,
                        std::function<DynamicValue()>(&makeStellar)); 

A Prettier Way
--------------
I don't like the factory.  I don't know why, it just makes me feel bad.  You
can see another way, though, once you observe that `resultsFactory` is not just
a function that returns a `Results`, it's any code at all that happens to
return a `Results`.  So, in addition to providing a hook for the user to give
us a particular `Results`, we've also provided a hook to do whatever they want
at that point in the API's operation.

The user gives us a callback that takes a `Results`, but in general we don't
know how to create a `Results` suitable for putting results into, and so the
user additionally gives us a `Results` factory.  So it's:

1. Execute my query.
2. When the results are ready, call my factory to get a `Results` object.
3. Fill the `Results` object with the results.
4. Call my callback.

**But the following would accomplish the same thing**:

1. Execute my query.
2. When the results are ready, call my (different) callback with a function
   that takes `Results`.
3. I'll create `Results` object and call your continuation with it (or not).

In code, this alternative contract looks like this:

    class DatabaseAccessor {

        template <typename Results>
        using Callback = 
            std::function<void(const std::function<void(Results&)>&)>;

        template <typename Results, typename Parameters>
        void asyncQuery(const std::string_view&  query,
                        const Callback<Results>& callback,
                        const Parameters&        parameters);
    };

That hurts my head a little at first.  `Callback<Results>` is a function that
returns `void` and takes as its one argument a function that returns `void`
and takes as its one argument a `Results&`.

Seeing it used helps:

    void onResponse(const std::function<void(DynamicValue&)> fillResults) {
        DynamicValue results(parseSchema("fpml_exotics.xsd"), "Stellar");
        fillResults(results);
        // ...
    }

    database.asyncQuery("execute GetContract(@id, @client);",
                        DatabaseAccessor::Callback<Results>(&onResponse), 
                        params);

Notice how I use the `DatabaseAccessor::Callback` alias to keep things short.

Isn't that cool?

It rolls off the tongue a bit more easily if you're willing to employ a macro:

    #define FN(...) std::function<void(__VA_ARGS__)>
    #define CB(...) const FN(__VA_ARGS__)&

This way, the signatures are easier to read:

    class DatabaseAccessor {

        template <typename Results, typename Parameters>
        void asyncQuery(const std::string_view&  query,
                        CB(CB(Results&))         callback,
                        const Parameters&        parameters);
    };

Though your willingness to use macros, especially with such short names, is a
matter of taste.

What's the Difference?
----------------------
Why choose one of the two styles above over the other? Is one better than the
other?

Yes, the second version of the asynchronous API is better.  Here's why:

### It's more procedural
The callback-in-a-callback solution has the user answer the question: "What
happens when the query results are available?"  Part of answering that question
is having a mechanism to fill an object with the results (that's the argument
to the callback).

The factory solution has the user answer two questions:

1. What happens when the results are available and I've filled a `Results`
   object with them?

2. How do I create a `Results` object?

with the understanding that a certain sequence of operations involving the
answers to the two questions will be carried out by the library.  Better to
give the user what they need and have them do what they want.

Of course, in the case where default constructing a `Results` object is the
right thing, it's convenient to have a version of the API that does this for
you, since then the API looks more like a function:

    makeQuery :: Query -> Results

But that's not the general case.

### It's just a different kind of callback
This is an aesthetic argument rather than a technical one, but I like that the
synchronous flavors of the API take a single output argument, and the
asynchronous flavors of the API take a single callback argument.  Whether the
user or the library needs to provide a `Results` object is decided by the
signature of the callback, rather than by the presence or absence of an
additional factory argument. 

## Part Two
If this sort of thing interests you, then take a look at [part 2][part2].

[bdlat]: https://bloomberg.github.io/bde/group__bdlat.html
[part2]: callbacks2.html
