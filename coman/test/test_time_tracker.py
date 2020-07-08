from coman.time_tracker import TimeTracker, FutureTimePoint

import pytest


def test_future_time_point_comparison():
    t = TimeTracker()
    tt = TimeTracker()
    a = t.after(1)
    b = t.after(5)
    c = t.after(5)
    d = tt.after(3)
    e = tt.after(1)

    assert a < b == c
    assert d > e
    with pytest.raises(ValueError):
        a > d
    with pytest.raises(ValueError):
        a == e
    with pytest.raises(TypeError):
        a != 1
