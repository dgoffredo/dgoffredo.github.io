Channels
========
![](site/chan.png)

I implemented [Go-style channels and select][chan] in C++. The need doesn't
arise often, but when it does, it's frustrating not to be able to multiplex
operations easily.

But [Boost][boost] already implements channels! And why not just use
[asio][asio]? And if you care so much about multiplexing operations on
logical threads of execution, why not just use [Go][go] instead of C++?
What, you're going to use use _kernel_ threads for this? Won't that use too
many resources? Aren't you concerned about the cost of context switching? What
about the [C10k problem][c10k]? Besides, you probably don't even need
channels. You should just do things another way. Why are you reinventing the
wheel? Don't you know anything?

Okay, okay.  Your concerns are valid, but things are going to be fine.
Computers are fun.

Motivation
----------
Back when I was writing a [C++ wrapper library][ipc] for
[POSIX message queues][mq], I was frustrated by how difficult it was to
portably consume a message queue while also being able to stop on demand.  The
simplest consumer I could imagine, "consume messages from this queue until I
tell you to stop," in general requires the use of UNIX signals, since in
general POSIX message queues are not files, and so cannot be used in IO
multiplexing facilities like [poll][poll].  Sure, you could send a special
message to the queue, "okay, stop now," but that works only if you are the only
consumer.  You wouldn't want your "stop" message to go to some other consumer.

Fortunately, on Linux it is the case that POSIX message queues _are_ files,
and so I can use `poll` to block on the condition that _either_ a message
arrives on the queue _or_ somebody pokes me to tell me to stop. I could make
a [pipe][pipe] on which the consumer would "poll" for reads, so that when I
wanted to tell the consumer "stop," I'd just [write][write] to the pipe. The
consumer would then handle that event by ceasing its queue consuming
activities.

What do I write to the pipe? Anything really. What if I wanted to
communicate more than just "stop," though? Maybe there are other commands
I'd like to send to the queue-consuming thread. I could invent a protocol of
messages to encode onto the pipe, and then the queue-consuming thread would
parse them on the other end. That would be silly, though, since the consumer
is in the same address space as the "stopper."  Instead, it would be better to
coordinate the copying/moving of a "command" object from one location to
another, using the pipe only to wake a possibly sleeping thread.

Now what if I had more than one thread that wanted to send a command to the
consumer?  Well, they would contend for some mutex and thus each would have to
wait its turn.

I could even add a more contrived requirement that a thread be able to send
such a command to one of multiple consumers, whichever is available first.
Regardless, the abstraction that is coming into focus from this combination of
`poll`ing files and copying objects is a [_channel_][channel].  Let the mutex,
the pipe, and `poll` all be implementation details of a mechanism for
_exchanging a value with another thread_.  Further, I want to be able to
perform one out of possibly many exchanges, with only one occurring between any
two threads at a given time.

`select(...)`
-------------
In [Go][go], the facility for doing exactly one send/receive operation from a
set of possible channels is called [select][go-select].  I like that name, so
let's use it.

The thing is, we're not concerned solely with sending and receiving on
channels.  In the motivating example, above, one of the operations is to
receive from a POSIX message queue.  Or, possibly I want to read/write on a
FIFO, or wait for some timeout to expire, or accept on a socket.  We need a
more general notion of `select` than Go provides.

Also, as a library writer in C++, I can't change the language itself.  What
should the C++ analog of Go's select statement look like?  My favorite idea,
from [this project][c-chan], is to use a [switch statement][switch]:
```c++
switch (select(file.read(&buffer), chan1.send(thing), chan2.recv(&message))) {
    case 0:  // successfully read data from `file`
    case 1:  // successfully sent `thing` to `chan1`
    case 2:  // successfully received `message` from `chan2`
    default: // an error occurred
}
```

For the naughty-minded among you: _no_, you can't use preprocessor macros to
make something more like Go's select statement.  Not without lambda
expressions and additional overhead, anyway.

Concurrent ML
-------------
Go is not the only language with channels.  It is likely the most popular, and
the reason why so many other languages are now adding similar facilities of
their own (e.g. [Clojure][clojure-channels]).

I enjoy [Scheme][scheme]. One of its variants with which I have the most
[experience][dgoffredo-racket], [Racket][racket], has a `select`-like
facility, called [sync][racket-sync], that works with all kinds of things,
not just channels. The "things" it works with are deemed "events," and
evidently there's a whole [calculus][cml], called "Concurrent ML," for
composing events and synchronizing threads of execution with them (see
[this][wingolog], [this][wingotalk], and [this][cml-slides]).

I did not implement Concurrent ML in C++. It's a little beyond my grasp.
What I _did_ take from Concurrent ML, though, is the idea that my
synchronization primitive, `select`, will operate on _events_, not on
channels.

Events
------
What is an event?  To me, it's a state machine.  Under the hood, a thread will
be blocking in a call to `poll`, but the events determine which files will be
monitored by `poll`.

Let an `IoEvent` be a notion of the sort of thing `poll` can monitor (like the
[pollfd][pollfd] structure, but including timeouts and not depending on any
system headers), together with a special value indicating "I'm done."  Then I
call an _event_ any object that supports the following three operations:

- `IoEvent file()`: Give me something to wait on in `poll`.
- `IoEvent fulfill(IoEvent)`: The indicated `IoEvent` is available now.  Either
  give me another (or the same) `IoEvent` to wait on, or otherwise indicate
  that you are done (have been fulfilled).
- `void cancel(IoEvent)`: Somebody else was fulfilled before you, so clean up
  whatever you might have been doing.  Here's the most recent `IoEvent` you
  gave me to wait on.

That's it!  Then a sketch of how `select` works is straightforward:

    def select(events):
        ioEvents = [event.file() for event in events]
        while True:
            poll(ioEvents)
            for i, (ioEvent, event) in enumerate(zip(ioEvents, events)):
                if ioEvent.ready:
                    ioEvent = ioEvents[i] = event.fulfill(ioEvent)
                    if ioEvent.fulfilled:
                        for ioEvent, loser in zip(ioEvents, events):
                            if loser is not event:
                                loser.cancel(ioEvent)
                        return event

The trick, then, is to express sending to or receiving from a channel as one
such _event_.

The Original Channel Design
---------------------------
I don't know how to implement channel send events and receive events using the
framework described above.  I _thought_ that I did, but there's an essential
piece missing that, I think, makes `select`ing on channel events impossible.

Here was my original design.  A channel contains a mutex, a queue of senders,
and a queue of receivers.  Each sender or receiver has two pipes: one for
communicating with that sender/receiver, and another for responding to whoever
was writing to the sender/receiver.

The _event_ member functions for a sender or receiver could then look like
this:

- `IoEvent file()`: Lock the channel mutex and add myself to the relevant queue
  (sender queue if I'm a sender, etc.).  If I'm not the first in line, or if
  there is nobody in the other queue, then return an `IoEvent` that's the read
  end of my pipe.  I'm waiting for somebody to visit me.

  If I am first in line and there is somebody at the front of the other queue,
  then write a `HI` message to their pipe, and then return an `IoEvent` that's
  the read end of their reply pipe.  I'm waiting for them to respond.

- `IoEvent fulfill(IoEvent)`: Read a message (byte) from the pipe in the
   indicated `IoEvent` and proceed based on the message:
   - `HI`: Somebody wants to exchange a value with me.  Write `READY` to my
     reply pipe _and then do a blocking read on my pipe_.  A blocking read
     seems counter-productive, but it is necessary.  Were I instead to return
     to `poll`, it could be that another event is fulfilled on my thread
     before, during, or after the other thread performs the exchange, and so
     at best there's a possibility that two events are fulfilled (a violation
     of `select`'s semantics), and at worst the other read reads from or writes
     to invalid memory, as I have already moved past the `select` call.

     The result of this blocking read will be one of the following messages:
     `DONE`, `CANCEL`, or `ERROR`. `DONE` means done.  I can return an
     `IoEvent` indicating that I am fulfilled and `select` will return to
     the caller.  First, though, I must look again at the channel to see
     whether there's anybody I need to `POKE` &#x2014; more on that later.
     `CANCEL` means that the other thread fulfilled a different event, and
     so I must revisit the channel to see whether I can contact another
     thread or if I must wait to be visited by another thread.  `ERROR` means
     that an exception was thrown on the other thread while it attempted to
     exchange the value, and so I too should report an error on my thread
     (perhaps by throwing an exception).

   - `READY`: I had contacted another thread about exchanging a value, and now
     that thread is ready for the exchange.  Copy/move the object to/from
     their storage and then send them either a `DONE` or `ERROR` message,
     depending on how it goes.

   - `CANCEL`: I had contacted another thread about exchanging a value, but
     now that thread has fulfilled another event.  I must revisit the channel
     to see whether I can contact another thread or if I must wait to be
     visited by another thread.

   - `POKE`: I was not first in line, but then those in front of me finished
     and so now I am in front.  I should visit the channel to see whether
     there is anybody I can exchange a value with.

- `void cancel(IoEvent)`: Another event was fulfilled on my thread.  Write a
  `CANCEL` message to whoever I was interacting with, visit the channel and
  remove myself from the queue, possibly `POKE` the guy behind me, and return.

I thought that this was a good protocol, and it mostly works.  The fatal flaw
takes the form of a deadlock.

Suppose you have two threads, _thread1_ and _thread2_, selecting on two
channels, _chan1_ and _chan2_.  The following situation can produce a deadlock
some minority of the time.

On _thread1_:

    switch (select(chan1.send(value), chan2.recv(&destination))) {
        // ...
    }

On _thread2_:

    switch (select(chan2.send(value), chan1.recv(&destination))) {
        // ...
    }

That is, _thread1_ is sending to _chan1_ and receiving from _chan2_, while
_thread2_ is doing the opposite &#x2014; sending to _chan2_ and receiving from
_chan1_.

What causes the deadlock is that blocking read in `IoEvent fulfill(IoEvent)`.
Here's one possible interleaving that causes a deadlock.

| _thread1_                      | _thread2_                      |
| ---------                      | ---------                      |
| sit in _chan1_                 | sit in _chan2_                 |
| say `HI` on _chan2_            | say `HI` on _chan1_            |
| got `HI` on _chan1_            | got `HI` on _chan2_            |
| **block** for reply on _chan1_ | **block** for reply on _chan2_ |

![](site/sad-panda.png)

For comparison, what happens more often is the following:

| _thread1_                      | _thread2_                      |
| ---------                      | ---------                      |
| sit in _chan1_                 | sit in _chan2_                 |
| say `HI` on _chan2_            | say `HI` on _chan1_            |
| got `HI` on _chan1_            |                                |
| **block** for reply on _chan1_ | got `READY` on _chan1_         |
|                                | transfer value over _chan1_    |
|                                | say `DONE` on _chan1_          |
| got `DONE` on _chan1_          |                                |

![](site/happy-panda.png)

Here there's no deadlock; instead, _chan1_ "won the race."  How can I avoid the
deadlocking case?

No amount of protocol tweaking is enough to fix this problem.  In order to have
the "exactly one event is fulfilled" guarantee, a send/receive event must
perform a blocking read at some point, and doing so could cause a deadlock when
`select` involves more than one channel.

The New Channel Design
----------------------
Deadlocked and forlorn, I looked to [Go's implementation][go-select-src] of
`select` for inspiration.  This [description][steroids] of Go channels, by
Dmitry Vyukov, was especially helpful.  In particular, he notes the following
(emphasis mine):

> There is another tricky aspect. We add select as waiter to several
> channels,
> **but we do not want several sync channel operations to complete
> communication with the select** (for sync channels unblocking completes
> successful communication). **In order to prevent this, select-related
> entries in waiter queues contain a pointer to a select-global state
> word.** Before unblocking such waiters other goroutines try to CAS(statep,
> nil, sg), which gives them the right to unblock/communicate with the
> waiter. If the CAS fails, goroutines ignore the waiter (it’s being
> signaled by somebody else).

That's what I was missing!  In my original design, a thread interacting with
another thread over a channel had no notion of the _other events_ happening in
either thread's `select` call.  A thread must bring along with it a piece of
(as Dmitry put it) "select-global state," effectively allowing different events
in the same call to `select` to interact with each other.

While it's encouraging that there is a way to overcome the deadlock described
above, doing so spoils the simplicity of the original `select` implementation.

On the other hand, it simplifies the protocol described in the previous section
(`HI`, `READY`, `DONE`, etc.) since now a mutex will be used for coordinating
one side of the communication between two threads, rather than an additional
pipe.

### `EventContext`
Associated with each call to `select` will be an instance of the following
`struct`:
```c++
// `SelectorFulfillment` is a means by which an event in one `select`
// invocation can check or set the fulfillment of an event in a different
// `select` invocation.
struct SelectorFulfillment {
    // Note that, by convention, `&mutex` (the address of the `mutex`) will be
    // used to determine the locking order among two or more
    // `SelectorFulfillment::mutex`.
    Mutex mutex;

    enum State {
        FULFILLABLE,   // not fulfilled, and fulfillment is allowed
        FULFILLED,     // has already been fulfilled
        UNFULFILLABLE  // not fulfilled, but fulfillment is not allowed
    };

    State state;

    // key of the fulfilled event; valid only if `state == FULFILLED`
    EventKey fulfilledEventKey;
};
```

Channel send/receive events are then each given an `EventContext` by `select`,
where the `EventContext` contains the `EventKey` of that event, and a smart
pointer to the `select`'s `SelectorFulfillment`.  `EventContext` looks like
this:
```c++
struct EventContext {
    SharedPtr<SelectorFulfillment> fulfillment;
    // key of the event to which this `EventContext` was originally given
    EventKey eventKey;
};
```

An event can be given its `EventContext` as an argument to the one call to
`IoEvent file()`, so now the _event_ concept looks like this:

- `IoEvent file(const EventContext&)`
- `IoEvent fulfill(IoEvent)`
- `void cancel(IoEvent)`

Non-channel events, such as file reads/writes, can simply ignore the additional
`const EventContext&` argument.

Now, to make this new scheme work, there are three things that need to happen.

1. `select` keeps its `SelectorFulfillment::mutex` locked at all times _except_
   when it's blocked by `::poll`.  Effectively, we're implementing a condition
   variable &#x2014; but one that plays nice with file IO multiplexing.
   ```c++
   fulfillment.mutex.unlock();
   const int rc = ::poll(/*...*/);
   fulfillment.mutex.lock();
   ```
2. When a channel send/receive event wants to "visit" another thread, it does
   so by locking the other thread's `SelectorFulfillment`. Naively, this can
   cause another deadlock, where now instead of blocking each other on
   reading a pipe, threads could block each other acquiring a lock on each
   others' mutexes. The trick to avoiding this is always lock the mutexes in
   the same order. In particular, this means that if a thread's mutex comes
   _after_ the mutex of the thread it is trying to visit, it must first
   _unlock_ its mutex, then acquire a lock on the other mutex, and then re-lock
   its mutex. The initial unlocking of the thread's mutex prevents the
   deadlock.

   Once a visiting thread has acquired the two locks, it examines the
   `state` field of the other thread's `SelectorFulfillment`. If the `state`
   is `FULFILLABLE`, then the thread performs the transfer, marks the
   `state` `FULFILLED`, notes the `EventKey` of the other thread (so that
   `select` knows _who_ was fulfilled when that thread next awakens), and
   writes `DONE` to the other thread's pipe. If the `state` is not
   `FULFILLABLE`, then unlock that thread's mutex and try somebody else.
3. `select` checks its `SelectorFulfillment::state` after each call to `poll`,
   or any event's `file` or to `fulfill` member functions. It could be that
   during one of those calls, the event fulfilled an event on another
   thread, or it could be that the event momentarily relinquished the lock
   on its mutex and was fulfilled by another thread. Either way, `select`'s
   work is done. It can see which event was fulfilled by reading the
   `SelectorFulfillment::fulfilledEventKey` field, and proceed with cleanup.

Once I implemented these changes, the deadlock described in the previous
section went away.

`selectOnDestroy`
-----------------
For any of you still reading this (good job!), there were other morsels of C++
design that I encountered while working on this project.

For example, I want a channel's `send` and `recv` member functions to return
an _event_ object suitable for use as an argument to `select`:
```c++
switch (select(chan1.send(something), chan2.recv(&somethingElse))) {
    case 0: // ...
    case 1: // ...
    default: // ...
}
```

That's fine, but what if I want to perform a channel operation on its own, e.g.
```c++
chan1.send(something);
```
or
```c++
std::string message;
chan2.recv(&message);
```

How do I make sure that such calls actually _do_ something?  One option is to
have separate member functions instead:
```c++
chan1.doSend(something)

std::string message;
chan2.doRecv(&message);
```

That looks terrible.

At least with `recv` we could overload the member function to have a
no-argument version that just returns the received value:
```c++
std::string message = chan2.recv();
```

This wouldn't work for `send`, though.

The equivalent code using the existing `send` and `recv` would be:
```c++
select(chan1.send(something));

std::string message;
select(chan2.recv(&message));
```

That also looks terrible.

If only send/receive events could somehow _know_ whether they were part of a
`select` invocation.  If they could, then they could have the policy "if my
destructor is being called and I was never copied into a `select` call, then
call `select` with myself as the argument.

This way, code like this would still work:
```c++
select(chan1.send(something));  // Used in `select`; don't block in destructor
```
but so would this:
```c++
chan1.send(something);  // Not used in `select`; call `select` in destructor
```

For those of you currently thinking "that is a _terrible_ idea," I agree with
you.  Returning an object whose destructor then performs an operation is _not_
the same thing as performing an operation before returning.

Also, aren't we supposed to avoid blocking in destructors? I mean, look at
[what std::thread does][thread]. What about stack unwinding? Fortunately, a
destructor can detect whether there are currently any [exceptions in
flight][uncaught_exceptions]. It wouldn't surprise me if use of that
function is frowned upon, though.

Terrible idea or not, at least for the intended use case, the "history-aware
destructor" gets the job done.  My main concern would be that returned
temporaries are not destroyed until the "end of the full statement" in which
they were created, which would mean that if you create multiple send/receive
events as part of one complicated expression, the actual sends and receives
will all happen "at the semicolon," rather than at their call sites.  I just
don't see this being a problem, though, because there are only two reasons why
a `send` or `recv` would be part of a larger statement:

1. You're using them in `select`.  Fine, that's their intended use.
2. You're using their return values as input to some expression other than a
   call to `select`.  Like what?  The overloads in question don't return
   meaningful values, so in what situation would you compose them into a
   non-`select` expression?

So, the "history-aware destructor" solution is viable.  How do we implement it?

Let's ignore C++11's move semantics for now, and restrict ourselves to copies.
The signature of the copy constructor looks like this:
```c++
Object(const Object& other);
```
_`const`_ `Object`, so we can't modify the other object.  Then how are we
supposed to mark it as "don't block in your destructor"?  We'll have to use
`mutable`:
```c++
class Object {
    mutable bool selectOnDestroy = true;

  public:
    Object(const Object& other)
    : selectOnDestroy(other.selectOnDestroy) {
        other.selectOnDestroy = false;
    }

    ~Object() {
        if (selectOnDestroy && !std::uncaught_exceptions()) {
            select(*this);
        }
    }

    // ...
};
```

This breaks the idea of what it means to copy something.  Better would be to
make `Object` a move-only type, and modify `other.selectOnDestroy` in the move
constructor.  However, I want my library to support C++98, and so I'd need this
hack anyway.

Now,  how does an `Object` detect that it is being used in a call to
`select`?  We could set `selectOnDestroy = false` in the `file` member
function, but it's possible that `file` will never get called if another
event's `file` causes the `select` to be fulfilled.  What's needed is an
additional member function in the _event_ concept:
```c++
void touch() noexcept;
```
`touch` is guaranteed to be called exactly once on each _event_ before `file`
is called on anybody.  This way, each _event_ gets an opportunity to mark
itself `selectOnDestroy = false`:
```c++
void Object::touch() noexcept {
    selectOnDestroy = false;
}
```

With these changes, we support both usage styles for `send` and `recv`:
```c++
// block until we can send
chan1.send(something);

std::string message;
// block until we can receive
chan2.recv(&message);

// block until we can either send or receive, but not both
switch (select(chan1.send(somethingElse), chan2.recv(&message))) {
    case 0: // ...
    case 1: // ...
    default: // ...
}
```

Error Handling
--------------
I haven't mentioned how error handling works in this channels library.  Does
`select` throw exceptions?  Does it return special values indicating errors?
How does a client of `select` know when an error occurs, and which kind?

My first idea was just to have `select` throw an exception when an error
occurs.  The trouble with this is that then if a client wants to handle the
error immediately, they have to indent the entire select/switch construct in a
`try` block:
```c++
try {
    switch (select(...)) {
        case 0: // ...
        case 1: // ...
    }
}
catch (...) {
    // ...
}
```
This wouldn't bother me if it weren't for that fact that one of the strengths
of the select/switch combination is that the "handler" for each case is right
there in the switch statement.  Indenting the switch in order to catch
exceptions means indenting all of the "handler" code as well.

This problem goes away if the client allows the exception to propagate out of
the scope in which `select` was called, which is probably the common case, and
the benefit of exceptions generally.  However, I still consider the `try` block
too high a price to pay.

As an alternative, `select` can return negative values for errors, and
associated with each error code there can be a descriptive (though
non-specific) error message.  For example:
```c++
switch (const int rc = select(...)) {
    case 0: // ...
    case 1: // ...
    case 2: // ...
    default:
        std::cerr << "error in select(): " << errorMessage(rc) << "\n";
}
```

That looks okay.  But what if the client _wants_ an exception to be thrown?
For that, we can replace the `errorMessage(int)` function with a
`SelectError(int)` constructor:
```c++
switch (const int rc = select(...)) {
    case 0: // ...
    case 1: // ...
    case 2: // ...
    default:
        throw SelectError(rc);
}
```

This way, the extra code needed to use exceptions is just one statement.

So far so good, but there is still something missing.  My original idea of
using exceptions throughout had the added benefit that the `throw`er of the
exception can include runtime-specific information in the exception.  For
example, if copying/moving a value across a channel throws an exception, that
exact exception could be propagated to the caller of `select`.  Or, if the
error that occurred was at the system level, such as in the pthreads library,
then the relevant `errno` value could be included in the thrown exception.
This is not possible if all you have to work with is the _category_ of error
(one of the negative return values of `select`).

Is there a way to combine the "throw an exception only if you want" behavior
above with the "preserve information known only at the site of the error"
property of using exceptions throughout?

The only way I thought to reconcile them is by using a thread-local exception
object.  When an error occurs within a call to `select`, an exception is
thrown, but then rather than letting the exception escape, `select` instead
catches it and copies it to thread-local storage.  This way, clients of
`select` can do the following:
```c++
switch (select(...)) {
    case 0: // ...
    case 1: // ...
    case 2: // ...
    default:
        throw lastError();
}
```

Maybe you don't like the idea of using thread-local storage.  It feels like a
global variable.  It feels like a hack.  It feels dirty.

Hey, it works.

There's one more alternative that I considered.  Instead of returning
an integer, what if `select` returned some object _implicitly convertible_ to
an integer, but that also contained error information?
```c++
switch (Selection rc = select(...)) {
    case 0: // ...
    case 1: // ...
    case 2: // ...
    default:
        throw rc.exception();
}
```

Now there's no need for thread-local storage, because the exception object that
clients might want to throw can be stored in the `Selection` object returned
by `select`.  To be honest, I still prefer the thread-local version, but I
might implement this variant as well, for naysayers.

Supporting C++98 Sucks Without Boost
------------------------------------
I set out with the requirement that this channels library work with C++98 in
addition to more recent versions of the language.  One reason is simply the joy
of what I'll call "constraint driven design."  Another reason is that there are
droves of programmers out there still chained to dead-end platforms and
profitable balls of mud.  I highly doubt that any of those programmers are
about to start using my channels library in their legacy code, _but they could
if they wanted to_.

One easy way to support C++98 without losing your mind is use [boost][boost],
the grandfather of all C++ libraries.  Boost is both at the cutting edge of
what can be done with the language, _and_ provides portable C++98 versions of
various now-standard facilities.

Boost is also _big_.  That's not a viable excuse for my not using it, but
requiring clients of my library to have boost installed does contradict the
goal of providing a minimal, portable (except for Windows), self-contained
library.

An alternative to boost that I considered is [BDE][bde],
[Bloomberg][bloomberg]'s C++ library.  It's about half the size of boost, and
certainly implements all of the facilities I'd need for the channels library,
but BDE is not nearly as widely used as boost, uses its own version of
[parts of the standard library][bslstl], and
[does not seem to be maintained][commits].

Without boost or something like it, I'm on my own to use POSIX for whatever
I need.  At first I thought that this wouldn't be a big deal, but it ended up
consuming most of my development time.

Since you asked, here is the list of could-have-just-used-C++11 features that
I ended up implementing:

- [chan::Mutex][mutex]: Uses `pthread_mutex_t` under the hood.

- [chan::LockGuard][lockguard]: Works with a `chan::Mutex`.

- [chan::SharedPtr][sharedptr]: If `std::shared_ptr` is available, then it's
  just a type alias for that.  Otherwise, it's a minimal implementation that
  uses a `chan::Mutex` to protect its reference count.

- [chan::TimePoint][timepoint]: In order to specify timeouts, I needed kosher
  representations of points of time and intervals of time.  I could have just
  used `int milliseconds`, but this is C++ and we can do better.
  `chan::TimePoint` fills the same niche as
  [std::chrono::time_point][chrono-timepoint].

- [chan::Duration][duration]: Fills the same niche as
  [std::chrono::duration][chrono-duration].

- [chan::now][now]: Fills the same niche as
  [std::chrono::steady_clock][chrono-steadyclock].  I implemented it using
  POSIX's [CLOCK_MONOTONIC][clock-monotonic].  The C++ standardization
  committee [was right][rename] to call it `steady_clock` instead of
  `monotonic_clock`.  If a "monotonic" clock is used for measuring intervals,
  then what would be the point of having an unsteady monotonic clock?  I
  suppose you could use it to _order events_ relative to each other, but I'd
  say "clock" is too strong a word for a _counter_.  As far as I can tell
  from reading on the internet, `CLOCK_MONOTONIC` always happens to be a steady
  clock.

- [chan::shuffle][random]: Fills the same niche as
  [std::shuffle][std-shuffle].  In order to enforce fairness in breaking ties
  among multiple _events_ that might be fulfilled at the same time, `select`
  randomly permutes the order in which it visits events.  I couldn't just use
  C++98's `std::random_shuffle`, because it is not guaranteed to be thread
  safe.  Instead, I wrote my own `shuffle` that takes a pseudo-random number
  generator as an argument.  I had to implement the generator as well.

- [chan::Random15][random]: Fills the same niche as
  [std::linear_congruential_engine][std-lce].  I couldn't just use C++98's
  `std::rand()`, because it is not guaranteed to be thread safe.  I also
  couldn't use any of [POSIX's pseudo-random number generators][drand], because
  even those APIs that could get around the thread safety problem are sometimes
  [not implemented so][posix-rand].

- [chan::randomInt][random]: Fills the same niche as
  [std::uniform_int_distribution][std-uid].  If you need to restrict the range
  of values produced by a pseudo-random number generator, you must be careful
  not to introduce a bias in the output (such as is often the case if you use
  `operator%` to do the restricting).  The implementation uses
  [rejection sampling][rejection-sampling].

- [chan::systemRandom][random]: Fills the same niche as
  [std::random_device][std-randomdevice].  Pseudo-random numbers don't look
  very random if they are seeded with a constant.  Instead, I need a random
  starting value with which to seed the generator.  The implementation uses
  `/dev/urandom`.

- [chan::lastError][lasterror]: In order to implement the thread-local
  exception feature, described above, I had to simulate C++11's `thread_local`
  keyword.  Fortunately, every compiler under the sun supports the non-standard
  [__thread][__thread] keyword, so I just used that.  In addition to thread
  local storage, I also needed to make sure that the object I put there was
  properly aligned.  Without C++11's [std::aligned_storage][std-alignedstorage]
  or [std::max_align_t][std-maxalignt], I had to use a [union][lasterror-src]
  of all of the built-in numeric types supported by C++98.

- [CHAN_MAP][macros]: Since C++98 does not have
  [variadic templates][variadic-templates], if I want to support up to, say,
  nine arguments in `select`, then I have three options:

  1. Copy-paste nine nearly identical overloads of `select`, one for each arity.
  2. Use a code generator during an additional build stage to produce the
     repeated sections of the C++ source file.
  3. Use the preprocessor during compilation to generate the repeated sections
     of the C++ source file.

  I opted for option 3, and so there's a small library of preprocessor macros
  in [chan/macros/macros.h][macros], and their use in
  [chan/select/select.h][select] is a real eyesore, but at least I didn't
  repeat myself.

- [chan::currentThread][currentthread]: Fills the same niche as
  [std::this_thread::get_id()][std-getid].  I use it for debugging only.  The
  implementation uses [pthread_self][pthread-self].

I could have avoided implementing those twelve components if only I had
required C++11 or boost.  All together my implementations amount to an
additional 1173 lines of source.  That sounds like a lot, but considering that
it allows the library to support C++98 without depending on a large external
library, I think that it's justified.

More
----
That's enough of that.  If your curiosity is piqued, then you can
[get started][more] playing with C++ channels and see how you like it.

[chan]: https://github.com/dgoffredo/chan
[boost]: https://www.boost.org/doc/libs/1_70_0/libs/fiber/doc/html/fiber/synchronization/channels/unbuffered_channel.html
[asio]: https://think-async.com/Asio/
[go]: https://golang.org/
[c10k]: https://en.wikipedia.org/wiki/C10k_problem
[poll]: http://pubs.opengroup.org/onlinepubs/9699919799/functions/poll.html
[ipc]: https://github.com/dgoffredo/ipc
[mq]: http://man7.org/linux/man-pages/man7/mq_overview.7.html
[pipe]: http://pubs.opengroup.org/onlinepubs/9699919799/functions/pipe.html
[write]: http://pubs.opengroup.org/onlinepubs/9699919799/functions/write.html
[channel]: https://en.wikipedia.org/wiki/Channel_(programming)
[go-select]: https://gobyexample.com/select
[clojure-channels]: https://clojure.org/news/2013/06/28/clojure-clore-async-channels
[scheme]: https://en.wikipedia.org/wiki/Scheme_(programming_language)
[racket]: https://racket-lang.org/
[racket-sync]: https://docs.racket-lang.org/reference/sync.html
[cml]: https://en.wikipedia.org/wiki/Concurrent_ML
[wingolog]: https://wingolog.org/archives/2017/06/29/a-new-concurrent-ml
[wingotalk]: https://www.youtube.com/watch?v=7IcI6sl5oBc
[cml-slides]: http://www.cs.uchicago.edu/~jhr/papers/1996/mspls-slides-reppy.ps
[dgoffredo-racket]: https://github.com/dgoffredo?utf8=%E2%9C%93&tab=repositories&q=&type=&language=racket
[pollfd]: http://pubs.opengroup.org/onlinepubs/9699919799/basedefs/poll.h.html
[go-select-src]: https://github.com/golang/go/blob/master/src/runtime/select.go
[steroids]: https://docs.google.com/document/d/1yIAYmbvL3JxOKOjuCyon7JhW4cSv1wy5hC0ApeGMV9s/pub
[uncaught_exceptions]: https://en.cppreference.com/w/cpp/error/uncaught_exception
[thread]: https://en.cppreference.com/w/cpp/thread/thread/~thread
[c-chan]: https://github.com/tylertreat/chan#select-statements
[switch]: https://en.cppreference.com/w/cpp/language/switch
[boost]: https://www.boost.org/
[bde]: https://github.com/bloomberg/bde
[bloomberg]: https://github.com/bloomberg
[bslstl]:https://github.com/bloomberg/bde/tree/master/groups/bsl/bsl%2Bbslhdrs
[commits]: https://github.com/bloomberg/bde/commits/master
[mutex]: https://github.com/dgoffredo/chan/blob/master/src/chan/threading/mutex.h
[lockguard]: https://github.com/dgoffredo/chan/blob/master/src/chan/threading/lockguard.h
[sharedptr]: https://github.com/dgoffredo/chan/blob/master/src/chan/threading/sharedptr.h
[timepoint]: https://github.com/dgoffredo/chan/blob/master/src/chan/time/timepoint.h
[duration]: https://github.com/dgoffredo/chan/blob/master/src/chan/time/duration.h
[now]: https://github.com/dgoffredo/chan/blob/master/src/chan/time/timepoint.cpp
[chrono-timepoint]: https://en.cppreference.com/w/cpp/chrono/time_point
[chrono-duration]: https://en.cppreference.com/w/cpp/chrono/duration
[chrono-steadyclock]: https://en.cppreference.com/w/cpp/chrono/steady_clock
[rename]: http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2010/n3128.html
[clock-monotonic]: https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/time.h.html
[random]: https://github.com/dgoffredo/chan/blob/master/src/chan/select/random.h
[std-shuffle]: https://en.cppreference.com/w/cpp/algorithm/random_shuffle
[std-lce]: https://en.cppreference.com/w/cpp/numeric/random/linear_congruential_engine
[posix-rand]: https://www.evanjones.ca/random-thread-safe.html
[std-randomdevice]: https://en.cppreference.com/w/cpp/numeric/random/random_device
[std-uid]: https://en.cppreference.com/w/cpp/numeric/random/uniform_int_distribution
[drand]: http://pubs.opengroup.org/onlinepubs/9699919799/functions/erand48.html
[rejection-sampling]: https://en.wikipedia.org/wiki/Rejection_sampling
[macros]: https://github.com/dgoffredo/chan/blob/master/src/chan/macros/macros.h
[variadic-templates]: https://en.cppreference.com/w/cpp/language/parameter_pack
[select]: https://github.com/dgoffredo/chan/blob/master/src/chan/select/select.h
[currentthread]: https://github.com/dgoffredo/chan/blob/master/src/chan/debug/currentthread.h
[std-getid]: https://en.cppreference.com/w/cpp/thread/get_id
[pthread-self]: http://pubs.opengroup.org/onlinepubs/9699919799/functions/pthread_self.html
[__thread]: https://en.wikipedia.org/wiki/Thread-local_storage#C_and_C++
[std-alignedstorage]:https://en.cppreference.com/w/cpp/types/aligned_storage
[std-maxalignt]: https://en.wikipedia.org/wiki/Thread-local_storage#C_and_C++
[lasterror]: https://github.com/dgoffredo/chan/blob/master/src/chan/select/lasterror.h
[lasterror-src]: https://github.com/dgoffredo/chan/blob/master/src/chan/select/lasterror.cpp
[more]: https://github.com/dgoffredo/chan#more