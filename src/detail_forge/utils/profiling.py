"""Memory profiling utilities using tracemalloc.

Provides a lightweight wrapper around Python's built-in tracemalloc module
for peak memory measurement. No third-party dependencies required.

Usage::

    from detail_forge.utils.profiling import measure_peak_memory_mb

    peak_mb = measure_peak_memory_mb(my_function, arg1, kwarg=val)
    assert peak_mb < 100, f"Expected < 100MB, got {peak_mb:.1f}MB"
"""

from __future__ import annotations

import tracemalloc
from collections.abc import Callable
from typing import Any


def measure_peak_memory_mb(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> float:
    """Measure peak memory usage of a callable in megabytes.

    Uses tracemalloc to capture the maximum memory allocation during
    the function's execution. The tracemalloc snapshot is taken at
    the end of the call.

    Args:
        fn: Callable to profile.
        *args: Positional arguments forwarded to fn.
        **kwargs: Keyword arguments forwarded to fn.

    Returns:
        Peak memory usage in megabytes (MB).

    Example::

        peak = measure_peak_memory_mb(list, range(1_000_000))
        print(f"Peak: {peak:.2f} MB")
    """
    tracemalloc.start()
    try:
        fn(*args, **kwargs)
        _snapshot = tracemalloc.take_snapshot()
        _current, peak_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    return peak_bytes / (1024 * 1024)


class MemoryProfiler:
    """Context-manager based memory profiler.

    Usage::

        with MemoryProfiler() as prof:
            do_work()
        print(f"Peak: {prof.peak_mb:.2f} MB")
    """

    def __init__(self) -> None:
        self.peak_mb: float = 0.0
        self._peak_bytes: int = 0

    def __enter__(self) -> "MemoryProfiler":
        tracemalloc.start()
        return self

    def __exit__(self, *_: object) -> None:
        _current, self._peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        self.peak_mb = self._peak_bytes / (1024 * 1024)
