import timeit
from functools import wraps


async def arange(count):
    for i in range(count):
        yield(i)


def timer(function):
    @wraps(function)
    def wrapper_timer(*args, **kwargs):
        start_time = timeit.default_timer()
        value = function(*args, **kwargs)
        elapsed = timeit.default_timer() - start_time
        print(f'Function "{function.__name__}" took {elapsed} seconds to complete.')
        return value
    return wrapper_timer