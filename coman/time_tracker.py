"""Module dedicated to time tracking."""

from functools import total_ordering
from typing import Union, cast


@total_ordering
class FutureTimePoint:
    """A time point that is expected to occur after some time or has already passed."""

    def __init__(self, time_tracker: 'TimeTracker', time_point: float):
        """Construct a FutureTimePoint. Should not be called explicitly.

        Use `TimeTracker.after` to create a FutureTimePoint.

        Parameters:
            time_tracker -- the instance of TimeTracker to associate this time point with.
            time_point   -- the representation of a time point internal to TimeTracker.

        Does not raise exceptions.
        """

        self._time_tracker = time_tracker
        self._time_point = time_point

    def __repr__(self) -> str:
        return f'FutureTimePoint(time_tracker={self._time_tracker}, time_point={self._time_point})'

    def has_passed(self) -> bool:
        """Check if this time point has passed based on the data of the associated time tracker."""
        return self._time_tracker.elapsed_time() >= self._time_point

    def __eq__(self, other: object) -> bool:
        self._check_comparability(other)
        # Mypy cannot infer that `other` is an instance of FutureTimePoint at this point.
        other = cast(FutureTimePoint, other)
        return self._time_point == other._time_point

    def __lt__(self, other: object) -> bool:
        self._check_comparability(other)
        other = cast(FutureTimePoint, other)
        return self._time_point < other._time_point

    def _check_comparability(self, other: object) -> None:
        if not isinstance(other, FutureTimePoint):
            raise TypeError(f'Cannot compare a FutureTimePoint with a(n) {type(other).__name__}')
        if self._time_tracker is not other._time_tracker:
            raise ValueError(f'Cannot compare two FutureTimePoint\'s belonging to different time trackers')


class TimeTracker:
    """Class for tracking time points.

        You probably don't want to construct or use it explicitly. Use methods of CoroutineManager
        to work with coroutines and time."""

    def __init__(self) -> None:
        """Construct TimeTracker."""
        self._elapsed_time = 0.0

    def elapsed_time(self) -> float:
        """Return the time elapsed since the construction."""
        return self._elapsed_time

    def update(self, time_delta: float) -> None:
        """Assume `time_delta` seconds have passed since the last call.

        See the documentation for `CoroutineManager.update` to for more information.
        """

        self._elapsed_time += time_delta

    def after(self, time_delta: float) -> 'FutureTimePoint':
        """Return a FutureTimePoint that will occur `time_delta` seconds after the current time."""
        return FutureTimePoint(self, self.elapsed_time() + time_delta)
