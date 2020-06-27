from coman.util import consume_deque

from collections import deque
from dataclasses import dataclass
from typing import Generic, TypeVar, Dict, Callable, Any, Protocol


_Event = TypeVar('_Event')
_Event_contra = TypeVar('_Event_contra', contravariant=True)


class Subscriber(Generic[_Event_contra], Protocol):
    def __call__(self, event: _Event_contra) -> None:
        ...


def _call_subscriber(subscriber: Subscriber[_Event], event: _Event) -> None:
    subscriber(event)


class EventManager(Generic[_Event]):
    def __init__(self):
        self._subscriptions: Dict[_Event, deque[Subscriber[_Event]]] = {}

    def subscribe(self, event: _Event, subscriber: Subscriber[_Event]) -> None:
        self._subscriptions.setdefault(event, deque()).append(subscriber)

    def raise_event(self, event: _Event) -> None:
        subscribers = self._subscriptions.get(event, deque())
        consume_deque(subscribers, (lambda sub: _call_subscriber(sub, event)), consume_new_elements=False)
        if len(subscribers) == 0:
            del self._subscriptions[event]
