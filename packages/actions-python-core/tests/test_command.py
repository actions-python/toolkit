import unittest

from actions.core.command import issue_command
from tests.utils import capture_output


class TestCommand(unittest.TestCase):
    def test_command_only(self):
        self.assertEqual(
            capture_output(issue_command, "some-command", {}, ""),
            "::some-command::",
        )

    def test_command_escapes_message(self):
        # Verify replaces each instance, not just first instance
        self.assertEqual(
            capture_output(
                issue_command,
                "some-command",
                {},
                "percent % percent % cr \r cr \r lf \n lf \n",
            ),
            "::some-command::percent %25 percent %25 cr %0D cr %0D lf %0A lf %0A",
        )

        # Verify literal escape sequences
        self.assertEqual(
            capture_output(
                issue_command,
                "some-command",
                {},
                "%25 %25 %0D %0D %0A %0A",
            ),
            "::some-command::%2525 %2525 %250D %250D %250A %250A",
        )

    def test_command_escapes_property(self):
        # Verify replaces each instance, not just first instance
        self.assertEqual(
            capture_output(
                issue_command,
                "some-command",
                {
                    "name": (
                        "percent % percent % cr \r cr \r lf \n lf \n colon : "
                        "colon : comma , comma ,"
                    )
                },
                "",
            ),
            (
                "::some-command name=percent %25 percent %25 cr %0D cr %0D lf "
                "%0A lf %0A colon %3A colon %3A comma %2C comma %2C::"
            ),
        )

        # Verify literal escape sequences
        self.assertEqual(
            capture_output(
                issue_command,
                "some-command",
                {},
                "%25 %25 %0D %0D %0A %0A %3A %3A %2C %2C",
            ),
            (
                "::some-command::%2525 %2525 %250D %250D %250A %250A %253A "
                "%253A %252C %252C"
            ),
        )

    def test_command_with_message(self):
        self.assertEqual(
            capture_output(issue_command, "some-command", {}, "some message"),
            "::some-command::some message",
        )

    def test_command_with_message_and_properties(self):
        self.assertEqual(
            capture_output(
                issue_command,
                "some-command",
                {"prop1": "value 1", "prop2": "value 2"},
                "some message",
            ),
            "::some-command prop1=value 1,prop2=value 2::some message",
        )

    def test_command_with_one_property(self):
        self.assertEqual(
            capture_output(issue_command, "some-command", {"prop1": "value 1"}, ""),
            "::some-command prop1=value 1::",
        )

    def test_command_with_two_properties(self):
        self.assertEqual(
            capture_output(
                issue_command,
                "some-command",
                {"prop1": "value 1", "prop2": "value 2"},
                "",
            ),
            "::some-command prop1=value 1,prop2=value 2::",
        )

    def test_command_with_three_properties(self):
        self.assertEqual(
            capture_output(
                issue_command,
                "some-command",
                {"prop1": "value 1", "prop2": "value 2", "prop3": "value 3"},
                "",
            ),
            "::some-command prop1=value 1,prop2=value 2,prop3=value 3::",
        )

    def test_should_handle_issuing_commands_for_non_string_objects(self):
        self.assertEqual(
            capture_output(
                issue_command,
                "some-command",
                {"prop1": {"test": "object"}, "prop2": 123, "prop3": True},
                {"test": "object"},
            ),
            (
                '::some-command prop1={"test"%3A"object"},prop2=123,prop3=true'
                '::{"test":"object"}'
            ),
        )
