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
    def __init__(self) -> None:
        self._event_manager = EventManager()
        self._time_tracker = TimeTracker()
        self._delayed_events: List[Tuple[FutureTimePoint, Event]] = []

    @property
    def event_manager(self) -> EventManager:
        return self._event_manager

    def update(self, time_delta: float) -> None:
        self._time_tracker.update(time_delta)
        self._handle_delayed_events()

    async def sleep(self, duration: float) -> None:
        event = self.event_manager.unique_event()
        self.add_delayed_event(delay=duration, event=event)
        await self.wait_for_event(event)

    async def wait_for_event(self, event: Event) -> None:
        # A workaround around a Mypy's alleged inability to work properly with
        # generator-based coroutines
        await self._wait_for_event_impl(event)  # type: ignore

    @coroutine
    def _wait_for_event_impl(self, event: Event) -> GeneratorType:
        yield event

    def start(self, coro: CoroutineType) -> None:
        self.resume(coro)

    def resume(self, coro: CoroutineType) -> None:
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
        num_total = len(coroutines)
        num_completed = 0
        completion_events = [self.event_manager.unique_event() for i in range(num_total)]

        def increase_completed(event: Event) -> None:
            del event
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

            self.event_manager.raise_event(event)         # Otherwise, process it
            heapq.heappop(self._delayed_events)             # Remove the processed event from the heap

    def add_delayed_event(self, delay: float, event: Event) -> None:
        heapq.heappush(self._delayed_events, (self._time_tracker.after(delay), event))
