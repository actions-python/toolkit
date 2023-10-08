import contextlib
import io
import os
import sys
import typing
import unittest
import uuid
from unittest.mock import patch

from actions.core import _process
from actions.core.core import (
    ExitCode,
    add_path,
    debug,
    end_group,
    error,
    export_variable,
    get_boolean_input,
    get_input,
    get_multiline_input,
    get_state,
    group,
    is_debug,
    notice,
    save_state,
    set_command_echo,
    set_failed,
    set_output,
    set_secret,
    start_group,
    warning,
)
from tests.utils import (
    async_capture_output,
    capture_output,
    mock_env_with_temporary_file,
)


class TestCore(unittest.IsolatedAsyncioTestCase):
    delimiter: typing.Optional[str]
    uuid: typing.Optional[typing.Any]

    env_vars: typing.ClassVar[typing.Dict[str, str]] = {
        "my var": "",
        "special char var \r\n];": "",
        "my var2": "",
        "my secret": "",
        "special char secret \r\n];": "",
        "my secret2": "",
        "PATH": f"path1{os.pathsep}path2",
        # Set inputs
        "INPUT_MY_INPUT": "val",
        "INPUT_MISSING": "",
        "INPUT_SPECIAL_CHARS_'\t\"\\": "'\t\"\\ response ",
        "INPUT_MULTIPLE_SPACES_VARIABLE": "I have multiple spaces",
        "INPUT_BOOLEAN_INPUT": "true",
        "INPUT_BOOLEAN_INPUT_TRUE1": "true",
        "INPUT_BOOLEAN_INPUT_TRUE2": "True",
        "INPUT_BOOLEAN_INPUT_TRUE3": "TRUE",
        "INPUT_BOOLEAN_INPUT_FALSE1": "false",
        "INPUT_BOOLEAN_INPUT_FALSE2": "False",
        "INPUT_BOOLEAN_INPUT_FALSE3": "FALSE",
        "INPUT_WRONG_BOOLEAN_INPUT": "wrong",
        "INPUT_WITH_TRAILING_WHITESPACE": "  some val  ",
        "INPUT_MY_INPUT_LIST": "val1\nval2\nval3",
        "INPUT_LIST_WITH_TRAILING_WHITESPACE": "  val1  \n  val2  \n  ",
        # Save inputs
        "STATE_TEST_1": "state_val",
        # Set debug
        "RUNNER_DEBUG": "",
        # File Commands
        "GITHUB_PATH": "",
        "GITHUB_ENV": "",
        "GITHUB_OUTPUT": "",
        "GITHUB_STATE": "",
    }

    async def asyncSetUp(self):
        self.uuid = uuid.uuid4()
        self.delimiter = f"ghadelimiter_{self.uuid}"
        self.uuid_mocked = patch("uuid.uuid4", return_value=self.uuid)
        self.uuid_mocked.start()
        self.environ_mocked = patch.dict("os.environ", self.env_vars)
        self.environ_mocked.start()

    async def asyncTearDown(self):
        self.delimiter = None
        self.uuid = None
        self.uuid_mocked.stop()
        self.environ_mocked.stop()

    def test_legacy_export_variable_produces_the_correct_command_and_sets_the_env(self):
        self.assertEqual(
            capture_output(export_variable, "my var", "var val"),
            "::set-env name=my var::var val",
        )

    def test_legacy_export_variable_escapes_variable_names(self):
        self.assertEqual(
            capture_output(export_variable, "special char var \r\n,:", "special val"),
            "::set-env name=special char var %0D%0A%2C%3A::special val",
        )
        self.assertEqual(os.getenv("special char var \r\n,:"), "special val")

    def test_legacy_export_variable_escapes_variable_values(self):
        self.assertEqual(
            capture_output(export_variable, "my var2", "var val\r\n"),
            "::set-env name=my var2::var val%0D%0A",
        )
        self.assertEqual(os.getenv("my var2"), "var val\r\n")

    def test_legacy_export_variable_handles_boolean_inputs(self):
        self.assertEqual(
            capture_output(export_variable, "my var", True),
            "::set-env name=my var::true",
        )

    def test_legacy_export_variable_handles_number_inputs(self):
        self.assertEqual(
            capture_output(export_variable, "my var", 5), "::set-env name=my var::5"
        )

    def test_export_variable_produces_the_correct_command_and_sets_the_env(self):
        with mock_env_with_temporary_file("GITHUB_ENV") as f:
            capture_output(export_variable, "my var", "var val")
            f.assertFileEqual(
                self,
                (
                    f"my var<<{self.delimiter}{os.linesep}var val{os.linesep}"
                    f"{self.delimiter}{os.linesep}"
                ),
            )

    def test_export_variable_handles_boolean_inputs(self):
        with mock_env_with_temporary_file("GITHUB_ENV") as f:
            capture_output(export_variable, "my var", True)
            f.assertFileEqual(
                self,
                (
                    f"my var<<{self.delimiter}{os.linesep}true{os.linesep}"
                    f"{self.delimiter}{os.linesep}"
                ),
            )

    def test_export_variable_handles_number_inputs(self):
        with mock_env_with_temporary_file("GITHUB_ENV") as f:
            capture_output(export_variable, "my var", 5)
            f.assertFileEqual(
                self,
                (
                    f"my var<<{self.delimiter}{os.linesep}5{os.linesep}"
                    f"{self.delimiter}{os.linesep}"
                ),
            )

    def test_set_secret_produces_the_correct_command(self):
        self.assertEqual(
            capture_output(set_secret, "secret val"), "::add-mask::secret val"
        )
        self.assertEqual(
            capture_output(set_secret, "multi\nline\r\nsecret"),
            "::add-mask::multi%0Aline%0D%0Asecret",
        )

    def test_legacy_add_path_produces_the_correct_commands_and_sets_the_env(self):
        capture_output(add_path, "myPath")
        self.assertEqual(os.getenv("PATH"), f"myPath{os.pathsep}path1{os.pathsep}path2")

    def test_add_path_produces_the_correct_commands_and_sets_the_env(self):
        with mock_env_with_temporary_file("GITHUB_PATH") as f:
            capture_output(add_path, "myPath")
            self.assertEqual(
                os.getenv("PATH"), f"myPath{os.pathsep}path1{os.pathsep}path2"
            )
            f.assertFileEqual(self, f"myPath{os.linesep}")

    def test_get_input_gets_non_rqeuired_input(self):
        self.assertEqual(get_input("my input"), "val")

    def test_get_input_gets_rqeuired_input(self):
        self.assertEqual(get_input("my input", required=True), "val")

    def test_raises_get_input_on_missing_required_input(self):
        with self.assertRaisesRegex(
            Exception,
            "Input required and not supplied: missing",
        ):
            get_input("missing", required=True)

    def test_get_input_does_not_raise_on_missing_non_required_input(self):
        self.assertEqual(get_input("missing", required=False), "")

    def test_get_input_is_case_insensitive(self):
        self.assertEqual(get_input("My InPuT"), "val")

    def test_get_input_handles_special_characters(self):
        self.assertEqual(get_input("special chars_'\t\"\\"), "'\t\"\\ response")

    def test_get_input_handles_multiple_spaces(self):
        self.assertEqual(
            get_input("multiple spaces variable"), "I have multiple spaces"
        )

    def test_get_input_trims_whitespace_by_default(self):
        self.assertEqual(get_input("with trailing whitespace"), "some val")

    def test_get_input_trims_whitespace_when_option_is_explicitly_true(self):
        self.assertEqual(
            get_input("with trailing whitespace", trim_whitespace=True), "some val"
        )

    def test_get_input_trims_whitespace_when_option_is_false(self):
        self.assertEqual(
            get_input("with trailing whitespace", trim_whitespace=False), "  some val  "
        )

    def test_get_boolean_input_gets_non_rqeuired_input(self):
        self.assertTrue(get_boolean_input("boolean input"))

    def test_get_boolean_input_gets_rqeuired_input(self):
        self.assertTrue(get_boolean_input("boolean input", required=True))

    def test_get_boolean_input_handles_boolean_input(self):
        self.assertTrue(get_boolean_input("boolean input true1"))
        self.assertTrue(get_boolean_input("boolean input true2"))
        self.assertTrue(get_boolean_input("boolean input true3"))
        self.assertFalse(get_boolean_input("boolean input false1"))
        self.assertFalse(get_boolean_input("boolean input false2"))
        self.assertFalse(get_boolean_input("boolean input false3"))

    def test_get_boolean_input_handles_wrong_boolean_input(self):
        with self.assertRaisesRegex(
            Exception,
            (
                'Input does not meet YAML 1.2 "Core Schema" specification: '
                "wrong boolean input\n"
                "Support boolean input list: "
                "`true \\| True \\| TRUE \\| false \\| False \\| FALSE`"
            ),
        ):
            get_boolean_input("wrong boolean input")

    def test_get_multiline_input_works(self):
        self.assertListEqual(
            get_multiline_input("my input list"), ["val1", "val2", "val3"]
        )

    def test_get_multiline_input_trims_whitespace_by_default(self):
        self.assertListEqual(
            get_multiline_input("list with trailing whitespace"), ["val1", "val2"]
        )

    def test_get_multiline_input_trims_whitespace_when_option_is_explicitly_true(self):
        self.assertListEqual(
            get_multiline_input("list with trailing whitespace", trim_whitespace=True),
            ["val1", "val2"],
        )

    def test_get_multiline_input_trims_whitespace_when_option_is_false(self):
        self.assertListEqual(
            get_multiline_input("list with trailing whitespace", trim_whitespace=False),
            ["  val1  ", "  val2  ", "  "],
        )

    def test_legacy_set_output_produces_the_correct_command(self):
        self.assertEqual(
            capture_output(set_output, "some output", "some value"),
            f"{os.linesep}::set-output name=some output::some value",
        )

    def test_legacy_set_output_handles_bools(self):
        self.assertEqual(
            capture_output(set_output, "some output", False),
            f"{os.linesep}::set-output name=some output::false",
        )

    def test_legacy_set_output_handles_numbers(self):
        self.assertEqual(
            capture_output(set_output, "some output", 1.01),
            f"{os.linesep}::set-output name=some output::1.01",
        )

    def test_set_output_produces_the_correct_command_and_sets_the_output(self):
        with mock_env_with_temporary_file("GITHUB_OUTPUT") as f:
            capture_output(set_output, "my out", "out val")
            f.assertFileEqual(
                self,
                (
                    f"my out<<{self.delimiter}{os.linesep}out val{os.linesep}"
                    f"{self.delimiter}{os.linesep}"
                ),
            )

    def test_set_output_handles_boolean_inputs(self):
        with mock_env_with_temporary_file("GITHUB_OUTPUT") as f:
            capture_output(set_output, "my out", True)
            f.assertFileEqual(
                self,
                (
                    f"my out<<{self.delimiter}{os.linesep}true{os.linesep}"
                    f"{self.delimiter}{os.linesep}"
                ),
            )

    def test_set_output_handles_number_inputs(self):
        with mock_env_with_temporary_file("GITHUB_OUTPUT") as f:
            capture_output(set_output, "my out", 5)
            f.assertFileEqual(
                self,
                (
                    f"my out<<{self.delimiter}{os.linesep}5{os.linesep}"
                    f"{self.delimiter}{os.linesep}"
                ),
            )

    def test_set_failed_sets_the_correct_exit_code_and_failure_message(self):
        self.assertEqual(
            capture_output(set_failed, "Failure message"), "::error::Failure message"
        )
        self.assertEqual(_process.CURRENT_EXIT_CODE, ExitCode.FAILURE)

    def test_set_failed_escapes_the_failure_message(self):
        self.assertEqual(
            capture_output(set_failed, "Failure \r\n\nmessage\r"),
            "::error::Failure %0D%0A%0Amessage%0D",
        )
        self.assertEqual(_process.CURRENT_EXIT_CODE, ExitCode.FAILURE)

    def test_set_failed_handles_exception(self):
        self.assertEqual(
            capture_output(set_failed, Exception("this is my error message")),
            "::error::this is my error message",
        )
        self.assertEqual(_process.CURRENT_EXIT_CODE, ExitCode.FAILURE)

    def test_error_sets_the_correct_error_message(self):
        self.assertEqual(
            capture_output(error, "Error message"), "::error::Error message"
        )

    def test_error_escapes_the_error_message(self):
        self.assertEqual(
            capture_output(error, "Error message\r\n\n"),
            "::error::Error message%0D%0A%0A",
        )

    def test_error_escapes_the_exception(self):
        self.assertEqual(
            capture_output(error, Exception("this is my error message")),
            "::error::this is my error message",
        )

    def test_error_handles_parameters_correctly(self):
        self.assertEqual(
            capture_output(
                error,
                Exception("this is my error message"),
                {
                    "title": "A title",
                    "file": "root/test.txt",
                    "start_line": 5,
                    "end_line": 5,
                    "start_column": 1,
                    "end_column": 2,
                },
            ),
            (
                "::error title=A title,file=root/test.txt,line=5,endLine=5,col=1,"
                "endColumn=2::this is my error message"
            ),
        )

    def test_warning_sets_the_correct_message(self):
        self.assertEqual(capture_output(warning, "Warning"), "::warning::Warning")

    def test_warning_escapes_the_message(self):
        self.assertEqual(
            capture_output(warning, "\r\nwarning\n"), "::warning::%0D%0Awarning%0A"
        )

    def test_warning_handles_exception(self):
        self.assertEqual(
            capture_output(warning, Exception("this is my error message")),
            "::warning::this is my error message",
        )

    def test_warning_handles_parameters_correctly(self):
        self.assertEqual(
            capture_output(
                warning,
                Exception("this is my error message"),
                {
                    "title": "A title",
                    "file": "root/test.txt",
                    "start_line": 5,
                    "end_line": 5,
                    "start_column": 1,
                    "end_column": 2,
                },
            ),
            (
                "::warning title=A title,file=root/test.txt,line=5,endLine=5,col=1,"
                "endColumn=2::this is my error message"
            ),
        )

    def test_notice_sets_the_correct_message(self):
        self.assertEqual(capture_output(notice, "Notice"), "::notice::Notice")

    def test_notice_escapes_the_message(self):
        self.assertEqual(
            capture_output(notice, "\r\nnotice\n"),
            "::notice::%0D%0Anotice%0A",
        )

    def test_notice_handles_exception(self):
        self.assertEqual(
            capture_output(notice, Exception("this is my error message")),
            "::notice::this is my error message",
        )

    def test_notice_handles_parameters_correctly(self):
        self.assertEqual(
            capture_output(
                notice,
                Exception("this is my error message"),
                {
                    "title": "A title",
                    "file": "root/test.txt",
                    "start_line": 5,
                    "end_line": 5,
                    "start_column": 1,
                    "end_column": 2,
                },
            ),
            (
                "::notice title=A title,file=root/test.txt,line=5,endLine=5,col=1,"
                "endColumn=2::this is my error message"
            ),
        )

    def test_start_group_starts_a_new_group(self):
        self.assertEqual(capture_output(start_group, "my-group"), "::group::my-group")

    def test_end_group_ends_new_group(self):
        self.assertEqual(capture_output(end_group), "::endgroup::")

    async def test_group_wraps_an_async_call_in_a_group(self):
        async def async_lambda():
            sys.stdout.write("in my group\n")
            return True

        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            self.assertTrue(await group("mygroup", async_lambda))

        self.assertEqual(
            await async_capture_output(group, "mygroup", async_lambda),
            f"::group::mygroup{os.linesep}in my group\n::endgroup::",
        )

    async def test_group_wraps_an_sync_call_in_a_group(self):
        def sync_lambda():
            sys.stdout.write("in my group\n")
            return True

        with io.StringIO() as buf, contextlib.redirect_stdout(buf):
            self.assertTrue(await group("mygroup", sync_lambda))

        self.assertEqual(
            await async_capture_output(group, "mygroup", sync_lambda),
            f"::group::mygroup{os.linesep}in my group\n::endgroup::",
        )

    def test_debug_sets_the_correct_message(self):
        self.assertEqual(capture_output(debug, "Debug"), "::debug::Debug")

    def test_debug_escapes_the_message(self):
        self.assertEqual(
            capture_output(debug, "\r\ndebug\n"), "::debug::%0D%0Adebug%0A"
        )

    def test_legacy_save_state_produces_the_correct_command(self):
        self.assertEqual(
            capture_output(save_state, "state_1", "some value"),
            "::save-state name=state_1::some value",
        )

    def test_legacy_save_state_handles_bools(self):
        self.assertEqual(
            capture_output(save_state, "state_1", True),
            "::save-state name=state_1::true",
        )

    def test_legacy_save_state_handles_numbers(self):
        self.assertEqual(
            capture_output(save_state, "state_1", 1), "::save-state name=state_1::1"
        )

    def test_save_state_produces_the_correct_command_and_saves_the_state(self):
        with mock_env_with_temporary_file("GITHUB_STATE") as f:
            capture_output(save_state, "my state", "out val")
            f.assertFileEqual(
                self,
                (
                    f"my state<<{self.delimiter}{os.linesep}out val{os.linesep}"
                    f"{self.delimiter}{os.linesep}"
                ),
            )

    def test_save_state_handles_boolean_inputs(self):
        with mock_env_with_temporary_file("GITHUB_STATE") as f:
            capture_output(save_state, "my state", True)
            f.assertFileEqual(
                self,
                (
                    f"my state<<{self.delimiter}{os.linesep}true{os.linesep}"
                    f"{self.delimiter}{os.linesep}"
                ),
            )

    def test_save_state_handles_number_inputs(self):
        with mock_env_with_temporary_file("GITHUB_STATE") as f:
            capture_output(save_state, "my state", 5)
            f.assertFileEqual(
                self,
                (
                    f"my state<<{self.delimiter}{os.linesep}5{os.linesep}"
                    f"{self.delimiter}{os.linesep}"
                ),
            )

    def test_get_state_gets_wrapper_action_state(self):
        self.assertEqual(get_state("TEST_1"), "state_val")

    def test_is_debug_check_debug_state(self):
        self.assertFalse(is_debug())
        os.environ["RUNNER_DEBUG"] = "1"
        self.assertTrue(is_debug())

    def test_set_command_echo_can_enable_echoing(self):
        self.assertEqual(capture_output(set_command_echo, True), "::echo::on")

    def test_set_command_echo_can_disable_echoing(self):
        self.assertEqual(capture_output(set_command_echo, False), "::echo::off")
