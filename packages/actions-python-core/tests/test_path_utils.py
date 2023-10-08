import os
import unittest

from parameterized.parameterized import parameterized

from actions.core.path_utils import to_platform_path, to_posix_path, to_win32_path


class TestPathUtils(unittest.TestCase):
    @parameterized.expand(
        [
            ("empty string", "", ""),
            ("single value", "foo", "foo"),
            ("with posix relative", "foo/bar/baz", "foo/bar/baz"),
            ("with posix absolute", "/foo/bar/baz", "/foo/bar/baz"),
            ("with win32 relative", "foo\\bar\\baz", "foo/bar/baz"),
            ("with win32 absolute", "\\foo\\bar\\baz", "/foo/bar/baz"),
            ("with a mix", "\\foo/bar/baz", "/foo/bar/baz"),
        ]
    )
    def test_to_posix_path(self, _: str, input: str, expected: str):
        self.assertEqual(to_posix_path(input), expected)

    @parameterized.expand(
        [
            ("empty string", "", ""),
            ("single value", "foo", "foo"),
            ("with posix relative", "foo/bar/baz", "foo\\bar\\baz"),
            ("with posix absolute", "/foo/bar/baz", "\\foo\\bar\\baz"),
            ("with win32 relative", "foo\\bar\\baz", "foo\\bar\\baz"),
            ("with win32 absolute", "\\foo\\bar\\baz", "\\foo\\bar\\baz"),
            ("with a mix", "\\foo/bar/baz", "\\foo\\bar\\baz"),
        ]
    )
    def test_to_win32_path(self, _: str, input: str, expected: str):
        self.assertEqual(to_win32_path(input), expected)

    @parameterized.expand(
        [
            ("empty string", "", ""),
            ("single value", "foo", "foo"),
            ("with posix relative", "foo/bar/baz", os.path.join("foo", "bar", "baz")),
            (
                "with posix absolute",
                "/foo/bar/baz",
                os.path.join(os.sep, "foo", "bar", "baz"),
            ),
            ("with win32 relative", "foo\\bar\\baz", os.path.join("foo", "bar", "baz")),
            (
                "with win32 absolute",
                "\\foo\\bar\\baz",
                os.path.join(os.sep, "foo", "bar", "baz"),
            ),
            ("with a mix", "\\foo/bar/baz", os.path.join(os.sep, "foo", "bar", "baz")),
        ]
    )
    def test_to_platform_path(self, _: str, input: str, expected: str):
        self.assertEqual(to_platform_path(input), expected)
