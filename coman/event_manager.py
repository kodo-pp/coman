"""Module responsible for the event manager."""

from coman.util import consume_deque

from collections import deque
from dataclasses import dataclass
from typing import Generic, TypeVar, Dict, Callable, Any, Protocol, Hashable, Tuple, List, Deque


Event = Hashable


class Subscriber(Protocol):
    """A protocol representing a function that can be called in response to an event."""

    def __call__(self, event: Event) -> None:
        ...


class EventSelector(Protocol):
    """A protocol representing a function that can tell whether an event matches the expectations or not."""

    def __call__(self, event: Event) -> bool:
        ...


_Multisubscription = Tuple[EventSelector, Subscriber]


def _call_subscriber(subscriber: Subscriber, event: Event) -> None:
    subscriber(event)


class UniqueEvent:
    """An event that equals no other events.

    However, a UniqueEvent may equal some other UniqueEvent created by other EventManager than
    the creator of this one."""

    def __init__(self, nonce: int) -> None:
        """Construct a UniqueEvent with a specified nonce.

        Nonces must not be reused. However, coinciding nonces may be used when unique events are
        constructed by different event managers.

        Mose likely, you will not need to call this method from your code. Use EventManager's methods
        to construct instances of UniqueEvent.
        """
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
    """Event manager.

    There are two primary operations:

    (1) Subscribe for event. This operation registers a subscriber (usually a plain function)
        for an event that will be called when/if such event is raised. In fact, one can subscribe to
        multiple events at once, which is called multisubscription (when at least one matching event
        is raised, corresponding multisubscribers get called and removed from the multisubscription list,
        so triggering another matching event won't result in any more calls by default).
        If there are multiple (multi)subscribers for an event, and this event is raised, then
        no guarantees are given about the order in which the (multi)subscribers will be called.

    (2) Raise an event. This operation calls all the subscribers for a specific event and
        removes them from the subscription list. If it is necessary to handle an event repeatedly,
        one can re-subscribe for this event every time when the subscriber is called,
        but it is one-shot subscribtion that is desired most commonly.

    For more information, see the methods' documentation.
    """

    def __init__(self) -> None:
        """Construct an event manager.

        If you don't need a standalone event manager (not bound to a coroutine manager),
        you probably won't need to construct an EventManager object directly.
        CoroutineManager already contains an event manager, which is available as part
        of CoroutineManager's public API. This doesn't apply, however, if you only need
        the functionality of EventManager and not CoroutineManager.
        """

        self._subscriptions: Dict[Event, Deque[Subscriber]] = {}
        self._multisubscriptions: List[_Multisubscription] = []
        self._counter = 0

    def subscribe(self, event: Event, subscriber: Subscriber) -> None:
        """Subscribe to a single event.

        `subscriber` will be called when the event `event` is raised. The subscription acts
        in a one-shot manner, meaning that after `event` has been raised and `subscriber` has
        been called, the subscribtion is cancelled. One, however, can subscribe to this event
        again if needed.

        See the class documentation for more information.

        Parameters:
            event      -- the event to subscribe to.
            subscriber -- the function or callable object to call when `event` is raised.

        Unless there is a bug, thit method does not throw exceptions.
        """

        self._subscriptions.setdefault(event, deque()).append(subscriber)

    def multisubscribe(self, selector: EventSelector, subscriber: Subscriber) -> None:
        """Subscribe to multiple events.

        `subscriber` will be called when any event such that `selector(event) == True` is raised.
        After this happens, this multisubscription is cancelled, which means that if any other
        event satisfying `selector(event) == True` is raised, then `subscriber` will not be called
        again. However, it is possible to call `multisubscribe` again if it is desired to handle
        a set of events repeatedly.

        This method is not suitable for the scenario when you have a set of events and you want
        to handle each of them exactly once. If it is your case, you should call `subscribe`
        for each event in this set instead of using `multisubscribe`.

        See the class documentation for more information.

        Parameters:
            selector   -- a function that takes an event and returns True if `subscriber` should
                          handle this event and False otherwise.
            subscriber -- a function to be called when a matching event is raised.

        Unless there is a system/hardware failure (such as a memory allocation error), this method
        does not raise any exceptions.
        """

        self._multisubscriptions.append((selector, subscriber))

    def raise_event(self, event: Event) -> None:
        """Raise an event.

        All subscribers for this event are called and deleted from the subscription list.
        All multisubscribers whose `selector`s (see `multisubscribe`'s docs) return True on
        this event are also called and deleted from the multisubscription list.
        The order in which matching (multi)subscribers are called is not strictly defined
        and should not be relied on (even though the current implementation may give some guarantees
        about this order, we retain the possibility to change it).

        See the class documentation for more information.

        Parameters:
            event -- the event to raise.

        Unless a (multi)subscriber that is called raises an exception, there is a bug in the code
        or there is a system/hardware failure, this method does not raise exceptions.
        """

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
        """Returns an event that equals no other event (in the context of this EventManager, at least).

        For more information, see the documentation for UniqueEvent."""

        nonce = self._counter
        self._counter += 1
        return UniqueEvent(nonce)
