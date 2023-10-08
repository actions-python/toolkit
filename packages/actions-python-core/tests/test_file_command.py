import os
import typing
import unittest
import uuid
from unittest.mock import patch

from actions.core.file_command import issue_file_command, prepare_key_value_message
from tests.utils import mock_env_with_temporary_file


class TestFileCommand(unittest.TestCase):
    delimiter: typing.Optional[str]
    uuid: typing.Optional[typing.Any]

    def setUp(self):
        self.uuid = uuid.uuid4()
        self.delimiter = f"ghadelimiter_{self.uuid}"
        self.uuid_mocked = patch("uuid.uuid4", return_value=self.uuid)
        self.uuid_mocked.start()

    def tearDown(self):
        self.delimiter = None
        self.uuid = None
        self.uuid_mocked.stop()

    def test_issue_file_command(self):
        with mock_env_with_temporary_file("GITHUB_STATE") as f:
            issue_file_command("STATE", "test")
            f.assertFileEqual(self, f"test{os.linesep}")

    def test_raises_if_delimiter_in_name(self):
        error_message = (
            "Unexpected input: name should not contain the delimiter "
            f'"{self.delimiter}"'
        )

        with self.assertRaisesRegex(Exception, error_message):
            prepare_key_value_message(f"{self.delimiter}", "value")

        with self.assertRaisesRegex(Exception, error_message):
            prepare_key_value_message(f"prefix{self.delimiter}", "value")

        with self.assertRaisesRegex(Exception, error_message):
            prepare_key_value_message(f"{self.delimiter}suffix", "value")

    def test_raises_if_delimiter_in_value(self):
        error_message = (
            "Unexpected input: value should not contain the delimiter "
            f'"{self.delimiter}"'
        )

        with self.assertRaisesRegex(Exception, error_message):
            prepare_key_value_message("key", f"{self.delimiter}")

        with self.assertRaisesRegex(Exception, error_message):
            prepare_key_value_message("key", f"prefix{self.delimiter}")

        with self.assertRaisesRegex(Exception, error_message):
            prepare_key_value_message("key", f"{self.delimiter}suffix")

    def test_prepare_key_value_message_with_none(self):
        self.assertEqual(
            prepare_key_value_message("foo", None),
            f"foo<<ghadelimiter_{self.uuid}\n\n{self.delimiter}",
        )

    def test_prepare_key_value_message_with_string_value(self):
        self.assertEqual(
            prepare_key_value_message("foo", "bar"),
            f"foo<<{self.delimiter}\nbar\n{self.delimiter}",
        )

    def test_prepare_key_value_message_with_json(self):
        self.assertEqual(
            prepare_key_value_message("foo", {"bar": "baz"}),
            f'foo<<{self.delimiter}\n{{"bar":"baz"}}\n{self.delimiter}',
        )
