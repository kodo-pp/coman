from coman.util import consume_deque

from collections import deque
from dataclasses import dataclass
from typing import Generic, TypeVar, Dict, Callable, Any, Protocol, Hashable, Tuple, List, Deque


Event = Hashable


class Subscriber(Protocol):
    def __call__(self, event: Event) -> None:
        ...


class EventSelector(Protocol):
    def __call__(self, event: Event) -> bool:
        ...


_Multisubscription = Tuple[EventSelector, Subscriber]


def _call_subscriber(subscriber: Subscriber, event: Event) -> None:
    subscriber(event)


class UniqueEvent:
    def __init__(self, nonce: int) -> None:
        self._nonce = nonce

    def __repr__(self) -> str:
        return f'UniqueEvent({self._nonce})'

    def __eq__(self, other: object) -> bool:
        return isinstance(other, UniqueEvent) and self._nonce == other._nonce

    def __hash__(self) -> int:
        # This 64-bit pseudorandom number is to distinguish between
        # `hash(UniqueEvent(nonce))` and `hash(('UniqueEvent', nonce))`
        return hash(('UniqueEvent', self._nonce)) ^ 0x67B59A64ECBF4986


class EventManager:
    def __init__(self) -> None:
        self._subscriptions: Dict[Event, Deque[Subscriber]] = {}
        self._multisubscriptions: List[_Multisubscription] = []
        self._counter = 0

    def subscribe(self, event: Event, subscriber: Subscriber) -> None:
        self._subscriptions.setdefault(event, deque()).append(subscriber)

    def multisubscribe(self, selector: EventSelector, subscriber: Subscriber) -> None:
        self._multisubscriptions.append((selector, subscriber))

    def raise_event(self, event: Event) -> None:
        # TODO: maybe refactor this function.

        # Deal with ordinary subscriptions.

        # Get the subscribers for the event in question.
        subscribers = self._subscriptions.get(event, None)
        # If there is no, do nothing here.
        if subscribers is not None:
            # Otherwise, delete all the subscribers existing at the current moment, calling each
            # of them in the process. That is, each subscriber for this event is called and then deleted.
            # If any of them cause new subscriptions for this event to appear, the new subscribers
            # will not be deleted or called: only they (if any) will remain in the `subscribers` deque.
            consume_deque(subscribers, (lambda sub: _call_subscriber(sub, event)), consume_new_elements=False)
            # After this, delete the entry of the `self._subscriptions` dictionary if it became empty.
            if len(subscribers) == 0:
                del self._subscriptions[event]

        # Now deal with multisubscriptions. TODO: maybe put this into a separate function?

        # A snapshot of currently existing multisubscriptions. The iteration will be done over this
        # copy so that new multisubscriptions that may appear during the iteration will not interfere
        # with the process.
        multisubscriptions_copy = self._multisubscriptions
        # We temporarily clear the `self._multisubscriptions` list so that after the iteration
        # only newly created multisubscriptions (if any) will live there. This is important because
        # each of the currently existing multisubscription may or may not be deleted in this process,
        # and the ones that persist are stored separately. This is all done to simplify this unobvious
        # process.
        self._multisubscriptions = []
        # The storage for multisubscriptions that are not deleted in the process.
        remaining_multisubscriptions: List[_Multisubscription] = []

        # Now, the process begins.
        for selector, subscriber in multisubscriptions_copy:
            # For each multisubscription (consisting of an event selector and a subscriber function)
            # decide whether to call the subscriber (and delete it) or to leave it intact (and retain it
            # in the list of multisubscriptions).
            if selector(event):
                # Call & delete (it isn't present in `self._multisubscriptions` or
                # `remaining_multisubscriptions`, and we are not adding it to any of them)
                subscriber(event)
            else:
                # Retain (store in a separate buffer for now)
                remaining_multisubscriptions.append((selector, subscriber))
        # After the process has finished, we have the following:
        #      `multisubscriptions_copy`: unchanged, but now unnecessary.
        #     `self._multisubscriptions`: newly created multisubscriptions (if any).
        # `remaining_multisubscriptions`: old multisubscriptions that haven't been called.
        # We need to retain old and new multisubscriptions (the order is not important,
        # but we maintain it in this implementation), so we simply join two of these lists.
        self._multisubscriptions = remaining_multisubscriptions + self._multisubscriptions

    def unique_event(self) -> Event:
        nonce = self._counter
        self._counter += 1
        return UniqueEvent(nonce)
