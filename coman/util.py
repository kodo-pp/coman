from collections import deque
from typing import TypeVar, Callable, Deque


_T = TypeVar('_T')


def consume_deque(
    d: Deque[_T],
    function: Callable[[_T], None],
    consume_new_elements: bool = True
) -> None:
    initial_size = len(d)
    i = 0

    termination_condition: Callable[[Deque[_T], int], bool] = (
        lambda d, i: len(d) == 0
    ) if consume_new_elements else (
        lambda d, i: len(d) == 0 or i >= initial_size
    )

    while not termination_condition(d, i):
        function(d.popleft())
        i += 1
