"""Exclusive ownership of local output paths across command invocations."""

import errno
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


@contextmanager
def output_lock(path: Path) -> Iterator[None]:
    """Hold a non-blocking OS lock beside a canonical output path.

    Keep the lock file in place: deleting it would let another process lock a
    different inode while the first is still owned. Closing the handle releases
    ownership, including when a process exits unexpectedly.
    """
    target = path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    lock_path = target.with_name(f".{target.name}.lock")
    with lock_path.open("a+b", buffering=0) as handle:
        try:
            if sys.platform == "win32":
                import msvcrt

                if handle.seek(0, os.SEEK_END) == 0:
                    handle.write(b"\0")
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            if error.errno in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                raise OSError(
                    f"Output {target} is already in use by another run. "
                    "Wait for it to finish or choose a different output."
                ) from error
            raise
        yield
