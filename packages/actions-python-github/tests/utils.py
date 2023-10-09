import contextlib
import io
import os
import sys
import typing

if sys.version_info < (3, 10):
    import typing_extensions

    P = typing_extensions.ParamSpec("P")
else:
    P = typing.ParamSpec("P")


def capture_output(
    func: typing.Callable[P, typing.Any],
    *args: P.args,
    **kwargs: P.kwargs,
) -> str:
    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            func(*args, **kwargs)
        return buf.getvalue().rstrip(os.linesep)
