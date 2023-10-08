import unittest
import unittest.mock

from actions.core.utils import to_command_properties, to_command_value


class TestUtils(unittest.TestCase):
    def test_to_command_value_with_none(self):
        self.assertEqual(to_command_value(None), "")

    def test_to_command_value_with_string(self):
        self.assertEqual(to_command_value("foo"), "foo")

    def test_to_command_value_with_json(self):
        self.assertEqual(to_command_value({"foo": "bar"}), '{"foo":"bar"}')

    def test_to_command_properties_with_zero_keys(self):
        self.assertDictEqual(to_command_properties({}), {})

    def test_to_command_properties_with_partial_keys(self):
        self.assertDictEqual(
            to_command_properties({"title": "foo"}),
            {
                "title": "foo",
                "file": None,
                "line": None,
                "endLine": None,
                "col": None,
                "endColumn": None,
            },
        )

    def test_to_command_properties_with_full_keys(self):
        self.assertDictEqual(
            to_command_properties(
                {
                    "title": "A title",
                    "file": "root/test.txt",
                    "start_line": 5,
                    "end_line": 5,
                    "start_column": 1,
                    "end_column": 2,
                }
            ),
            {
                "title": "A title",
                "file": "root/test.txt",
                "line": 5,
                "endLine": 5,
                "col": 1,
                "endColumn": 2,
            },
        )
