import functools
import time

from django.db import connection, reset_queries
from ajax_datatable.utils import trace


def query_debugger(func):

    @functools.wraps(func)
    def inner_func(*args, **kwargs):

        reset_queries()

        start_queries = len(connection.queries)

        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()

        end_queries = len(connection.queries)

        trace('{func}(): {num_queries} queries ({elapsed:.2f}s)'.format(
            func=func.__qualname__,
            num_queries=end_queries - start_queries,
            elapsed=end - start,
        ))

        return result

    return inner_func
