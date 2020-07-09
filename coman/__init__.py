"""A simple coroutine manager.

Coroutines can be started and suspended for a specified period of time or
until certain event or events arise. Multiple coroutines can be run at once,
thus creating parallelism (but not concurrency).

For more information about the supported features, see the documentation for
modules `coman.coroutine_manager` and `coman.event_manager` --- these are the
main two. `coman.time_tracker` contains some auxiliary methods to implement
the functionality of a coroutine manager, but they aren't normally exposed
to the user of this library. Other modules contain helper functions, which are
also of little use outside the implementation of this library.
"""
