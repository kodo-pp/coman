from coman.util import consume_deque

from collections import deque


def test_consume_deque():
    data = [1, 4, 5, 6, 8, 10, 17]
    arr = []
    d = deque(data)

    def consumer(x):
        arr.append(x)
        if x % 2 == 0:
            d.append(1000*x + 1)
        elif x == 17:
            d.append(16)

    consume_deque(d, consumer)
    assert arr == [1, 4, 5, 6, 8, 10, 17, 4001, 6001, 8001, 10001, 16, 16001]
    assert d == deque([])

    arr.clear()
    d.extend(data)
    consume_deque(d, consumer, consume_new_elements=False)
    assert arr == [1, 4, 5, 6, 8, 10, 17]
    assert d == deque([4001, 6001, 8001, 10001, 16])
