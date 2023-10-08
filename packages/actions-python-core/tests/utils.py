import contextlib
import io
import os
import sys
import tempfile
import typing
import unittest

if sys.version_info < (3, 10):
    import typing_extensions

    P = typing_extensions.ParamSpec("P")
else:
    P = typing.ParamSpec("P")


class TemporaryFileAssert:
    def __init__(self, f: tempfile._TemporaryFileWrapper):
        self.f = f

    def assertFileEqual(  # noqa: N802
        self, test_case: unittest.TestCase, expr: str, msg: typing.Optional[str] = None
    ):
        """Check that the expression is same with file content."""
        with open(self.f.name, "r") as f:
            test_case.assertEqual(f.read(), expr, msg)


def capture_output(
    func: typing.Callable[P, typing.Any],
    *args: P.args,
    **kwargs: P.kwargs,
) -> str:
    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            func(*args, **kwargs)
        return buf.getvalue().rstrip(os.linesep)


async def async_capture_output(
    func: typing.Callable[P, typing.Coroutine[typing.Any, typing.Any, typing.Any]],
    *args: P.args,
    **kwargs: P.kwargs,
) -> str:
    with io.StringIO() as buf:
        with contextlib.redirect_stdout(buf):
            await func(*args, **kwargs)
        return buf.getvalue().rstrip(os.linesep)


@contextlib.contextmanager
def mock_env_with_temporary_file(name: str):
    with tempfile.NamedTemporaryFile("w", delete=False) as f:
        os.environ[name] = f.name
        yield TemporaryFileAssert(f)
        if os.path.isfile(f.name):
            os.remove(f.name)
        if name in os.environ:
            del os.environ[name]
