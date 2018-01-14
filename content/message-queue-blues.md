Message Queue Blues
===================
Imagine a portable, local, available, and minimal message queue: like a file or
a socket, but instead of reading from or writing to it, or receiving from or
sending to it, you enqueue to and dequeue from it.  You are not the first
person to imagine such a thing.  There are several ways to do it, but first
some requirements.

Requirements
------------
Here's what I'm looking for.

### Portable
This message queue needs to work on any UNIX-like system (sorry, Microsoft):
Linux, BSD variants, OS X, HP-UX, Solaris, and AIX at least.  Practically this
means that it must use only those facilities in POSIX.  Additionally, the queue
must be accessible from a variety of programming languages and environments
without much adaptation effort.  Ideally this means a file-like interface.

### Local
The queue does not need to be accessible outside of the machine in which it was
created.  I'm looking for a system-persistent (possibly gone on restart) IPC
mechanism.

### Available
The queue cannot depend on the operation of a singleton daemon (such as a
broker process in `init.d`), and must be available as soon as process Id 1 can
fork, possibly with the additional requirement that a file system is mounted.
This rules out things like Redis, RabbitMQ, and ZeroMQ.

### Minimal
Any source code above the system level must be short enough to read and
understand in one sitting, and trivial to build and deploy with default
development tools (e.g. no CMake, non-default compilers or libraries, etc.). 

Implementation Options
----------------------
A few possible solutions to this problem come to mind.  There are no doubt
others, but here's what I considered.

### Regular File with File Locking and Polling
Just use sqlite!  Job done, right?  Almost.  Sqlite (or any other regular-file-
based IPC) requires a writer to hold a lock; nobody else can write _or read_
when the lock is held by a writer.

Technically, using sqlite would violate the _minimal_ requirement, above,
because you can't read and understand it all in one sitting.  However, it's
tempting to use because it works out of the box with python, can be dropped
into any C/C++ build with a single `.c` file, and has bindings to many other
languages.

So how might you implement a queue this way?  First attempt -- a database
containing a single table "Queue":

    create table Queue(
        Id      integer primary key not null,
        Message text                not null);
                       

For example:

    Id      Message                
    ---     -------                
    1       "I was enqueued first."
    2       "Then I was enqueued." 
    3       "I am most recent."    

That's ID as in "identity," not the word "id."  Then a dequeue looks like this:

    begin immediate transaction;

followed by

    select Id, Message from Queue order by Id limit 1;

If we get something, then we have to remove it from the queue:

    delete from Queue where Id = @Id;

and in either case finish the transaction:

    commit transaction;
    
In this scheme, if the queue is empty, our only recourse is to commit the
transaction, sleep a bit, and then try again.  A more complicated protocol
could get around this, so that a dequeuer is notified when a message is
available for it.  I discuss this in another section.

The enqueue operation is simpler:

    begin immediate transaction;
    insert into Queue(Message) values(@Message);
    commit transaction;

Not so hard, right?  But there are problems:

1. Polling sucks.

2. There's no concept of fairness in which dequeuer gets the next message.

3. Sqlite's lock-the-world strategy could starve enqueuers or dequeuers, and
   will slow to a crawl under high contention.

Still, if the numbers of enqueuers, dequeuers, and messages are low, and if
there are ready-made bindings to sqlite available for your languauages of
choice, then this is a viable option.

It has the added benefit that the queue is persistent across system restart,
so long as the database file is on a persistent drive.

### Regular File with File Locking and Notification Pipes
For the price of added complexity, we can remove polling from the sqlite-based
local message queue.  The idea is that when a dequeuer sees that the queue is
empty, it adds itself to a list of waiting dequeuers, identifying itself using
a path to a pipe (fifo) that it has open for reading.

Then _en_queuers have the added responsibility on enqueue of checking whether
the queue is currently empty.  If it is, then in addition to enqueueing their
message they must also remove the oldest waitlist record, open the associated
pipe for writing, but _non-blocking_ so that they can detect if the dequeuer is
no longer waiting, write the ID of the message or the message itself to the
pipe, and then close the pipe.

There are all sorts of problems with this way of doing it, but it does
eliminate polling.  A lock is taken on the database file exactly once per
enqueue and at most once per dequeue.

### UNIX Domain Socket with Client-Provided Server
I said in the requirements section that solutions like ZeroMQ were inadequate
because they require a dedicated process to act as the broker or keeper of the
queue.

There is a way around this, though.  You can decentralize the responsibility of
spawning a broker at the cost of complicating what clients of the message queue
must do to access it.  Here's how:

Associate a UNIX domain socket with the message queue.  When a client wants to
enqueue or dequeue, he tries to connect to the socket.  If that fails, he
deletes the socket, fork/exec a known program, e.g.
`/usr/bin/local-queue-broker`, passing it the path to the (deleted) domain
socket.  `local-queue-broker` will try to listen on the socket.  If it
succeeds, then it continues to execute as the broker of the message queue.  If
it fails, then it exits.  The parent process, meanwhile, keeps trying to
connect, sleeping briefly between each failure.

When a broker is not running, clients will race to delete the socket, and then
their broker child processes will race to listen on the socket.  One broker
will win, and this will be the new broker.  In this way, clients can coordinate
the establishment or reestablishment of a broker.

But what a pain in the ass.

### Shared Memory
TODO (mention [boost/interprocess/ipc/message\_queue][boost-mq])

### POSIX Message Queues
TODO An introduction that sets up the next section.

POSIX Message Queues
--------------------
TODO All of the pain.

Signals and System Calls
------------------------
TODO The nitty gritty.

Using The Message Queue from Guile
----------------------------------
TODO Some scheme code.

Code
----
TODO Mention the `mq` repository.

[boost-mq]: https://github.com/boostorg/interprocess/blob/develop/include/boost/interprocess/ipc/message_queue.hpp
