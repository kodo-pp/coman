"""Main module responsible for the coroutine manager."""

from coman.event_manager import EventManager, Event
from coman.time_tracker import TimeTracker, FutureTimePoint

import heapq
from collections.abc import Iterable as IterableABC
from types import coroutine
from typing import List, Coroutine, Generator, Iterable, Callable, Union, Tuple

_YieldType = Union[Event, Iterable[Event], Callable[[Event], bool]]
CoroutineType = Coroutine[_YieldType, None, None]
GeneratorType = Generator[_YieldType, None, None]


class CoroutineManager:
    """Coroutine manager.

    This is the focus point for all the coroutine work done in this library.
    Coroutines managed by `coman` are started, suspended and resumed here.
    Hence, in order for a coroutine to be possible to get suspended and/or resumed,
    it must have access to the CoroutineManager object that stared it.

    It is important that a coroutine that was started by some instance of CoroutineManager
    does not use any other instances of CoroutineManager for suspension/resumption.
    If it does, no guarantees are given about the behavior of the program. It may work
    as expected, it may silently fail to do its job, hang, freeze or crash with an exception.
    This is because such things depend very much on the implementation of CoroutineManager,
    and we want to retain some flexibility in changing it while not breaking the code that
    relies on some implementation-specific behavior. In future versions, however, the
    consequences of such usage of CoroutineManager may become more deterministic.
    """

    def __init__(self) -> None:
        """Construct a coroutine manager."""
        self._event_manager = EventManager()
        self._time_tracker = TimeTracker()
        self._delayed_events: List[Tuple[FutureTimePoint, Event]] = []

    @property
    def event_manager(self) -> EventManager:
        """Return the EventManager object used to handle events."""
        return self._event_manager

    def update(self, time_delta: float) -> None:
        """Update the internal state and sleeping coroutines assuming `time_delta` seconds have passed.

        This method gives the CoroutineManager some flexibility in that it is not bound to the real
        pace of time. If it is desired to work in real time, then this method should be called
        in a loop where on each iteration `time_delta` equals the amount of time passed since the last
        iteration. Otherwise, it is possible to simulate the pace of time by passing any desired values
        of `time_delta`, and CoroutineManager will assume that exactly that much time has passed since
        `update` was last called (or the coroutine manager was constructed if it is the first call to
        `update`).

        Parameters:
            time_delta -- the amount of time (in seconds) CoroutineManager should assume to have passed
                          since (a) the last call to `update`, if any, or (b) the call to `__init__`,
                          if it is the first time `update` is called. Must be non-negative (this is
                          currently unchecked but may raise an exception in future versions).

        Unless an exception is raised by an event handler or a coroutine, this method does not raise
        exceptions. If it does, it is a bug or a system/hardware failure (out of memory error, for example).
        """

        self._time_tracker.update(time_delta)
        self._handle_delayed_events()

    async def sleep(self, duration: float) -> None:
        """Suspend the current coroutine for a specified amount of time.

        The coroutine will be resumed after `duration` "seconds", as assumed by the CoroutineManager.
        See the documentation for `update` method for more information about time tracking here.

        If two or more coroutines call `sleep` in such a way that they should wake up at the same time,
        no guarantees are given about the order in which they will be resumed.

        Parameters:
            duration -- the amount of time (in seconds) after which the coroutine will be resumed.
                        Must be non-negative (this is currently unchecked but may raise an exception
                        in future versions).

        Does not raise any exceptions.
        """

        event = self.event_manager.unique_event()
        self.add_delayed_event(delay=duration, event=event)
        await self.wait_for_event(event)

    async def wait_for_event(self, event: Event) -> None:
        """Suspend the current coroutine until a specified event is raised in the event manager.

        The current coroutine will be resumed when this event is raised in the event manager
        available as `CoroutineManager.event_manager`.

        If an event is raised while two or more coroutines are simultaneously waiting for it,
        no guarantees are given about the order in which they will be resumed.

        Parameters:
            event -- the event to wait for. See the documentation for `EventManager` for more information.

        Does not raise any exceptions.
        """

        # A workaround around a Mypy's alleged inability to work properly with
        # generator-based coroutines
        await self._wait_for_event_impl(event)  # type: ignore

    @coroutine
    def _wait_for_event_impl(self, event: Event) -> GeneratorType:
        yield event

    def start(self, coro: CoroutineType) -> None:
        """Start running a coroutine.

        Parameters:
            coro -- a coroutine as returned by an async function.

        Example:
        ```
        async def foo():
            ...

        cm = CoroutineManager()
        cm.start(foo())             # Notice that `foo` is called
        ```
        """

        self.resume(coro)

    def resume(self, coro: CoroutineType) -> None:
        """Resume a suspended coroutine started by this coroutine manager.

        Mostly used internally, but, to provide a little more flexibility, available
        in the public API.

        Parameters:
            coro -- coroutine object. See the documentation for `start` method for details and an example.

        Unless the coroutine raises an exception or there is a bug in the code, this method does not
        raise exceptions.
        """

        try:
            requested_event_selector = coro.send(None)
        except StopIteration:
            return

        resumer = lambda event: self.resume(coro)
        if isinstance(requested_event_selector, Event):
            self.event_manager.subscribe(event=requested_event_selector, subscriber=resumer)
        elif callable(requested_event_selector):
            self.event_manager.multisubscribe(selector=requested_event_selector, subscriber=resumer)
        else:
            assert isinstance(requested_event_selector, IterableABC)
            events_set = set(requested_event_selector)
            selector_function = lambda event: event in events_set
            self.event_manager.multisubscribe(selector=selector_function, subscriber=resumer)

    @coroutine
    def gather(self, coroutines: List[CoroutineType]) -> GeneratorType:
        """Create a coroutine that runs multiple coroutines in parallel.

        The coroutines will not be run at the same time in the strict sense since there is no
        concurrency among coroutines, but their execution will be parallel --- and not serial
        as it would be the case if they were awaited sequentially. Thus, the following two
        examples are equivalent:

        (1)
        ```
        async def foo(): ...
        async def bar(): ...

        cm = CoroutineManager()
        cm.run(foo())
        cm.run(bar())
        ```

        (2)
        ```
        async def foo(): ...
        async def bar(): ...

        cm = CoroutineManager()
        cm.run(cm.gather(foo(), bar()))
        ```

        Yet, calling `run` multiple times does not provide a coroutine that unites the execution
        of `foo` and `bar`, while what `gather` does is exactly this. That is, if
        `quux = cm.gather(foo(), bar())`, then awaiting `quux` will cause both `foo` and `bar`
        to be executed in parallel.

        Notice that `asyncio.gather` serves essentially the same purpose (but is not compatible
        with CoroutineManager and has certain differences with this implementation). To make sure
        that the purpose of this method is understood correctly, it is advised to take a look at
        the documentation for `asyncio.gather` and `asyncio` at the whole.

        When the returned coroutine is called, the constituent coroutines will be first called
        in the same order as they reside in the `coroutines` list. The order in which they are
        resumed afterward is governed by the functions that are used for their suspension (e.g.
        `wait_for_event` or `sleep`). Consult their documentation for details.

        Parameters:
            coroutines -- the list of coroutines to run in parallel.

        Unless a coroutine raises an exception or there is a bug in the code, this method does
        not raise any exceptions.
        """

        num_total = len(coroutines)
        num_completed = 0
        completion_events = [self.event_manager.unique_event() for i in range(num_total)]

        def increase_completed(event: Event) -> None:
            del event
            nonlocal num_completed
            num_completed += 1

        for event in completion_events:
            self.event_manager.subscribe(event=event, subscriber=increase_completed)

        for coro, event in zip(coroutines, completion_events):
            async def wrapped(coro: CoroutineType, completion_event: Event) -> None:
                await coro
                self.event_manager.raise_event(completion_event)

            self.start(wrapped(coro, event))

        while num_completed < num_total:
            yield completion_events

    def _handle_delayed_events(self) -> None:
        while len(self._delayed_events) > 0:
            time_point, event = self._delayed_events[0]     # Earliest delayed event
            if not time_point.has_passed():                 # Stop if the time for it still hasn't come
                break

            self.event_manager.raise_event(event)           # Otherwise, process it
            heapq.heappop(self._delayed_events)             # Remove the processed event from the heap

    def add_delayed_event(self, delay: float, event: Event) -> None:
        """Schedule an event to be raised after a specified amount of time.

        Mostly used internally, but in order to allow for greater flexibility, this method
        is exposed in the public API.

        Parameters:
            delay -- the amount of time (in seconds) after which the event will be raised.
            event -- the event to raise.

        Unless there is a bug in the code or a hardware/system failure, this method does not
        raise any exceptions.
        """

        heapq.heappush(self._delayed_events, (self._time_tracker.after(delay), event))
