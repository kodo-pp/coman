from functools import total_ordering
from typing import Union, cast


@total_ordering
class FutureTimePoint:
    def __init__(self, time_tracker: 'TimeTracker', time_point: float):
        self._time_tracker = time_tracker
        self._time_point = time_point

    def __repr__(self) -> str:
        return f'FutureTimePoint(time_tracker={self._time_tracker}, time_point={self._time_point})'

    def has_passed(self) -> bool:
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
    def __init__(self) -> None:
        self._elapsed_time = 0.0

    def elapsed_time(self) -> float:
        return self._elapsed_time

    def update(self, time_delta: float) -> None:
        self._elapsed_time += time_delta

    def after(self, time_delta: float) -> 'FutureTimePoint':
        return FutureTimePoint(self, self.elapsed_time() + time_delta)
