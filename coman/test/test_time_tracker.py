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


def test_time_tracker_elapsed_time():
    t = TimeTracker()
    assert t.elapsed_time() == 0
    t.update(2)
    assert t.elapsed_time() == 2
    t.update(5)
    assert t.elapsed_time() == 7


def test_time_tracker_after():
    t = TimeTracker()
    a = t.after(0)
    b = t.after(5)
    t.update(3)
    c = t.after(2)
    d = t.after(5)
    t.update(2)
    e = t.after(0)
    assert a < b == c == e < d


def test_future_time_point_has_passed():
    t = TimeTracker()
    a = t.after(0)
    b = t.after(1)
    c = t.after(3)
    assert a.has_passed()
    assert not b.has_passed()
    assert not c.has_passed()
    t.update(1)
    assert a.has_passed()
    assert b.has_passed()
    assert not c.has_passed()
    t.update(1)
    assert a.has_passed()
    assert b.has_passed()
    assert not c.has_passed()
    t.update(1)
    assert a.has_passed()
    assert b.has_passed()
    assert c.has_passed()
    t.update(100)
    assert a.has_passed()
    assert b.has_passed()
    assert c.has_passed()
