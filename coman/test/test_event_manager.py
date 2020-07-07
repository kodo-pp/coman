from coman.event_manager import EventManager


def make_functions(arr, em):
    def foo(event):
        arr.append(('foo', event))

    def bar(event):
        arr.append(('bar', event))

    def baz(event):
        arr.append(('baz', event))

    def quux(event):
        arr.append(('quux', event))
        em.subscribe(event=42, subscriber=baz)

    return foo, bar, baz, quux


def sel_all(event):
    return True


def sel_none(event):
    return False


def sel_string(event):
    return isinstance(event, str)


def sel_truthy(event):
    return bool(event)


def sel_greater_than_5(event):
    return isinstance(event, int) and event > 5


def test_subscribe():
    arr = []
    em = EventManager()

    foo, bar, baz, quux = make_functions(arr, em)

    em.subscribe(event='test_event_1', subscriber=foo)
    em.subscribe(event=42, subscriber=bar)
    em.subscribe(None, baz)  # None conveys no special meaning --- it's simply an event identifier
    em.subscribe(event=42, subscriber=quux)

    assert arr == []
    em.raise_event(None)
    assert arr == [('baz', None)]
    em.raise_event(42)
    assert arr == [('baz', None), ('bar', 42), ('quux', 42)]
    em.raise_event('does_not_exist')
    assert arr == [('baz', None), ('bar', 42), ('quux', 42)]
    em.raise_event(42)
    assert arr == [('baz', None), ('bar', 42), ('quux', 42), ('baz', 42)]
    em.raise_event(42)
    assert arr == [('baz', None), ('bar', 42), ('quux', 42), ('baz', 42)]
    em.raise_event('test_event_1')
    assert arr == [('baz', None), ('bar', 42), ('quux', 42), ('baz', 42), ('foo', 'test_event_1')]


def test_unique_event():
    arr = []
    em = EventManager()

    foo, bar, baz, quux = make_functions(arr, em)

    a = em.unique_event()
    b = em.unique_event()
    c = em.unique_event()
    d = 1
    e = 'event'
    f = em.unique_event()
    assert len({a, b, c, d, e, f}) == 6

    em.subscribe(a, foo)
    em.subscribe(b, bar)
    em.subscribe(c, foo)
    em.subscribe(d, baz)
    em.subscribe(e, bar)
    em.subscribe(f, baz)

    for ev in reversed([a, b, c, d, e, f]):
        em.raise_event(ev)

    assert arr == [
        ('baz', f),
        ('bar', e),
        ('baz', d),
        ('foo', c),
        ('bar', b),
        ('foo', a),
    ]


def test_multisubscribe():
    arr = []
    em = EventManager()

    foo, bar, baz, quux = make_functions(arr, em)

    em.subscribe(10, foo)
    em.subscribe(5, bar)
    em.multisubscribe(sel_greater_than_5, baz)
    em.raise_event(5)
    assert arr == [('bar', 5)]
    arr.clear()
    em.raise_event(10)
    assert set(arr) == {('foo', 10), ('baz', 10)}
    arr.clear()
    em.raise_event(6)
    assert arr == []

    em.multisubscribe(sel_all, foo)
    em.multisubscribe(sel_none, bar)
    em.multisubscribe(sel_string, baz)
    em.multisubscribe(sel_truthy, quux)

    em.raise_event(0)
    em.raise_event(5)
    em.multisubscribe(sel_truthy, quux)
    em.raise_event('hello')
    assert arr == [
        ('foo', 0),
        ('quux', 5),
        ('baz', 'hello'),
        ('quux', 'hello'),
    ]
