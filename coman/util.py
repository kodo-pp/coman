"""A module with some helper functions used internally."""

from collections import deque
from typing import TypeVar, Callable, Deque


_T = TypeVar('_T')


def consume_deque(
    d: Deque[_T],
    function: Callable[[_T], None],
    consume_new_elements: bool = True
) -> None:
    """Pop all the elements of deque and call a function on each of them (collectively, consume them).

    During the process, this function can push new elements onto the deque (extending it to the
    right). Depending on the arguments, such "new" elements may or may not be consumed alongside
    the old ones.

    Parameters:
        d                    -- the deque to act on.
        function             -- the function to call on each of the elements. This function can
                                append new elements to the deque, but must not touch existing
                                elements or append any elements to the left of the deque. That
                                is, it may call, for instance, `d.append` or `d.extend`, but
                                must not call `d.appendleft` or `d.extendleft` (this list is
                                non-exhaustive). If the function modifies the deque in any way
                                not approved here, no guarantees are given about the correctness
                                of the algorithm and the behavior of the program.
        consume_new_elements -- whether or not to consume "new" elements.
    """

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
