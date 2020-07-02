from functools import total_ordering
from typing import Union, cast


ComparisonResult = Union[bool, NotImplemented]


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
        if not self._is_comparable(other):
            return NotImplemented
        # Mypy cannot infer that `other` is an instance of FutureTimePoint at this point.
        other = cast(FutureTimePoint, other)
        return self._time_point == other._time_point

    def __lt__(self, other: object) -> ComparisonResult:
        if not self._is_comparable(other):
            return NotImplemented
        other = cast(FutureTimePoint, other)
        return self._time_point < other._time_point

    def _is_comparable(self, other: object) -> ComparisonResult:
        return isinstance(other, FutureTimePoint) and self._time_tracker is other._time_tracker


class TimeTracker:
    def __init__(self) -> None:
        self._elapsed_time = 0.0

    def elapsed_time(self) -> float:
        return self._elapsed_time

    def update(self, time_delta: float) -> None:
        self._elapsed_time += time_delta

    def after(self, time_delta: float) -> 'FutureTimePoint':
        return FutureTimePoint(self, self.elapsed_time() + time_delta)
