from coman.coroutine_manager import CoroutineManager


def test_delayed_events():
    cm = CoroutineManager()
    arr = []

    def foo(event):
        arr.append(('foo', event))

    def bar(event):
        arr.append(('bar', event))

    def baz(event):
        arr.append(('baz', event))

    cm.event_manager.subscribe(event='a', subscriber=foo)
    cm.event_manager.subscribe(event='b', subscriber=bar)
    cm.event_manager.subscribe(event='c', subscriber=baz)

    cm.add_delayed_event(delay=2, event='a')
    cm.add_delayed_event(delay=5, event='b')
    cm.add_delayed_event(delay=5, event='c')

    assert arr == []
    cm.update(0)
    assert arr == []
    cm.update(1)
    assert arr == []
    cm.update(1)
    assert arr == [('foo', 'a')]
    cm.update(2)
    assert arr == [('foo', 'a')]
    cm.update(1)
    assert arr == [('foo', 'a'), ('bar', 'b'), ('baz', 'c')]
    cm.update(100000)
    assert arr == [('foo', 'a'), ('bar', 'b'), ('baz', 'c')]


def test_wait_for_event():
    cm = CoroutineManager()
    arr = []

    async def foo():
        arr.append(1)
        await cm.wait_for_event('a')
        arr.append(2)
        await cm.wait_for_event('b')
        arr.append(3)

    assert arr == []
    cm.start(foo())
    assert arr == [1]
    cm.event_manager.raise_event('x')
    assert arr == [1]
    cm.event_manager.raise_event('a')
    assert arr == [1, 2]
    cm.event_manager.raise_event('a')
    assert arr == [1, 2]
    cm.event_manager.raise_event('b')
    assert arr == [1, 2, 3]
