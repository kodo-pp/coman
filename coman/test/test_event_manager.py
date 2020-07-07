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

    return {'foo': foo, 'bar': bar, 'baz': baz, 'quux': quux}


def test_subscribe():
    arr = []
    em = EventManager()

    funcs = make_functions(arr, em)
    foo = funcs['foo']
    bar = funcs['bar']
    baz = funcs['baz']
    quux = funcs['quux']

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
