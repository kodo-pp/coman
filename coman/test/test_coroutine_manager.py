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


def test_wait_for_event_multiple_coroutines():
    cm = CoroutineManager()
    arr = []

    async def foo():
        arr.append(1)
        await cm.wait_for_event('a')
        arr.append(2)
        await cm.wait_for_event('b')
        arr.append(3)

    async def bar():
        arr.append(4)
        await cm.wait_for_event('b')
        arr.append(5)
        await cm.wait_for_event('b')
        arr.append(6)

    assert arr == []
    cm.start(foo())
    cm.start(bar())
    assert set(arr) == {1, 4}
    cm.event_manager.raise_event('x')
    assert set(arr) == {1, 4}
    cm.event_manager.raise_event('a')
    assert set(arr) == {1, 2, 4}
    cm.event_manager.raise_event('a')
    assert set(arr) == {1, 2, 4}
    cm.event_manager.raise_event('b')
    assert set(arr) == {1, 2, 3, 4, 5}
    cm.event_manager.raise_event('b')
    assert set(arr) == {1, 2, 3, 4, 5, 6}
    cm.event_manager.raise_event('b')
    assert set(arr) == {1, 2, 3, 4, 5, 6}


def test_sleep():
    cm = CoroutineManager()
    arr = []

    async def foo():
        arr.append(1)
        await cm.sleep(2)   # 2
        arr.append(2)
        await cm.sleep(5)   # 7
        arr.append(3)

    async def bar():
        arr.append(4)
        await cm.sleep(3)   # 3
        arr.append(5)
        await cm.sleep(1)   # 4
        arr.append(6)
        await cm.sleep(10)  # 14
        arr.append(7)

    cm.start(foo())
    cm.start(bar())

    assert arr == [1, 4]
    cm.update(1)  # 1
    assert arr == [1, 4]
    cm.update(1)  # 2
    assert arr == [1, 4, 2]
    cm.update(1)  # 3
    assert arr == [1, 4, 2, 5]
    cm.update(1)  # 4
    assert arr == [1, 4, 2, 5, 6]
    cm.update(1)  # 5
    assert arr == [1, 4, 2, 5, 6]
    cm.update(2)  # 7
    assert arr == [1, 4, 2, 5, 6, 3]
    cm.update(6)  # 13
    assert arr == [1, 4, 2, 5, 6, 3]
    cm.update(1)  # 14
    assert arr == [1, 4, 2, 5, 6, 3, 7]
