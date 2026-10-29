"""Cooperative scan cancellation, scoped to the current worker only."""
from contextlib import contextmanager
from contextvars import ContextVar


class ScanCancelled(Exception):
    """A superseded or closing scan must stop without publishing an error."""


_cancel=ContextVar('pler_scan_cancel',default=None)


def checkpoint():
    event=_cancel.get()
    if event is not None and event.is_set():
        raise ScanCancelled()


@contextmanager
def cancellation(event):
    token=_cancel.set(event)
    try:
        checkpoint()
        yield
    finally:
        _cancel.reset(token)
