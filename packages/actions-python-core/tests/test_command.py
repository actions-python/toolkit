import unittest

from actions.core.command import issue, issue_command
from tests.utils import capture_output


class CommandTestCase(unittest.TestCase):
    def test_issue_command(self):
        self.assertEqual(
            capture_output(issue_command, "name", {"key": "value"}, "message"),
            "::name key=value::message",
        )

        self.assertEqual(
            capture_output(issue_command, "name", {"foo": "a", "bar": "b"}, "message"),
            "::name foo=a,bar=b::message",
        )

    def test_issue(self):
        self.assertEqual(capture_output(issue, "name", "message"), "::name::message")

    def test_escape_data(self):
        self.assertEqual(
            capture_output(
                issue_command,
                "some-command",
                {},
                "percent % percent % cr \r cr \r lf \n lf \n",
            ),
            "::some-command::percent %25 percent %25 cr %0D cr %0D lf %0A lf %0A",
        )

        self.assertEqual(
            capture_output(
                issue_command,
                "some-command",
                {},
                "%25 %25 %0D %0D %0A %0A",
            ),
            "::some-command::%2525 %2525 %250D %250D %250A %250A",
        )

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

    def test_escape_property(self):
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
