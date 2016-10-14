# cappy
Simple (for learning) capabilities based RPC protocol.

## Goal

Write some code using a [capabilities system](https://en.wikipedia.org/wiki/Object-capability_model) to get a feeling for how they work.


## Game plan

1.  Write a basic system.
    *   Don't worry too much about parsing the data.
        Do something simple and make whatever simplifying assumptions we
        want about the incoming bytes.
    *   Pick a well-used encoding (i.e. json) and don't worry about abstracting
        over the encoding at all.

    *   Don't worry about event loops or the network layer at all, but do think
        about what should return Futures so that event-loopy things can be done
        later.

    *   Identify the capabilities protocol itself: how do participants pass
        references as arguments to remote calls, etc. Focus entirely on this
        aspect of the problem.

2.  Abstract over the RPC service.
Don't worry about auto-generating stubs, but do write code that allows a developer to implement an interface and plug it into a system expecting an implementation of that interface.
3.  Abstract over the encoding and add in at least one nicely done specific example (again, json is a good choice).
4.  Hook everything up to a real asynchronous system (i.e. Netty) and make a chat server or something as an example.
