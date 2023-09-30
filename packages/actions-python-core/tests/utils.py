import contextlib
import io
import os
import typing

P = typing.ParamSpec("P")


def capture_output(
    func: typing.Callable[P, None], *args: P.args, **kwargs: P.kwargs
) -> str:
    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            func(*args, **kwargs)
        return buf.getvalue().rstrip(os.linesep)
