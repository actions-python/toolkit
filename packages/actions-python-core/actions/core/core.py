import asyncio
import enum
import os
import sys
import typing

from actions.core._compat import Unpack
from actions.core.command import issue, issue_command
from actions.core.file_command import issue_file_command, prepare_key_value_message
from actions.core.oidc_utils import OidcClient
from actions.core.utils import to_command_properties, to_command_value

T = typing.TypeVar("T")


class InputOptions(typing.TypedDict, total=False):
    """
    Interface for getInput options
    """

    # Whether the input is required. If required and not present, will raise.
    required: bool

    # Whether leading/trailing whitespace will be trimmed for the input.
    trim_whitespace: bool


class ExitCode(enum.IntEnum):
    """
    The code to exit an action
    """

    # A code indicating that the action was successful
    SUCCESS = 0

    # A code indicating that the action was a failure
    FAILURE = 1


class AnnotationProperties(typing.TypedDict, total=False):
    """
    Optional properties that can be sent with annotation commands (notice,
    error, and warning)
    See: https://docs.github.com/en/rest/reference/checks#create-a-check-run for
    more information about annotations.
    """

    # A title for the annotation.
    title: str

    # The path of the file for which the annotation should be created.
    file: str

    # The start line for the annotation.
    start_line: int

    # The end line for the annotation. Defaults to `start_line` when
    # `start_line` is provided.
    end_line: int

    # The start column for the annotation. Cannot be sent when `start_line` and
    # `end_line` are different values.
    start_column: int

    # The end column for the annotation. Cannot be sent when `start_line` and
    # `end_line` are different values.
    # Defaults to `start_column` when `start_column` is provided.
    end_column: int


def export_variable(name: str, val) -> None:
    """
    Sets env variable for this action and future actions in the job
    :param name: the name of the variable to set
    :param val: the value of the variable. Non-string values will be converted
                to a string via json.dumps
    """
    converted_value = to_command_value(val)
    os.environ[name] = converted_value

    file_path = os.getenv("GITHUB_ENV")
    if file_path:
        return issue_file_command("ENV", prepare_key_value_message(name, val))

    issue_command("set-env", {"name": name}, converted_value)


def set_secret(secret: str) -> None:
    """
    Registers a secret which will get masked from logs
    :param secret: value of the secret
    """
    issue_command("add-mask", {}, secret)


def add_path(input_path: str) -> None:
    """
    Prepends inputPath to the PATH (for this action and future actions)
    :param input_path:
    """
    file_path = os.getenv("GITHUB_PATH")
    if file_path:
        issue_file_command("PATH", input_path)
    else:
        issue_command("add-path", {}, input_path)
    os.environ["PATH"] = f'{input_path}{os.pathsep}{os.getenv("PATH")}'


def get_input(name: str, **options: Unpack[InputOptions]) -> str:
    """
    Gets the value of an input.
    Unless trimWhitespace is set to false in InputOptions, the value is also trimmed.
    Returns an empty string if the value is not defined.
    :param name: name of the input to get
    :param options: See InputOptions.
    """
    value = os.getenv(f"INPUT_{name.replace(' ', '_').upper()}", "")
    if options.get("required") and not value:
        raise Exception(f"Input required and not supplied: {name}")

    if not options.get("trim_whitespace", True):
        return value

    return value.strip()


def get_multiline_input(name: str, **options: Unpack[InputOptions]) -> typing.List[str]:
    """
    Gets the values of an multiline input. Each value is also trimmed.
    :param name: name of the input to get
    :param options: See InputOptions.
    """
    inputs = [i for i in get_input(name, **options).splitlines() if i != ""]

    if not options.get("trim_whitespace", True):
        return inputs

    return [i.strip() for i in inputs]


def get_boolean_input(name: str, **options: Unpack[InputOptions]) -> bool:
    """
    Gets the input value of the boolean type in the YAML 1.2 "core schema"
    specification.
    Support boolean input list: `true | True | TRUE | false | False | FALSE`.
    The return value is also in boolean type.
    ref: https://yaml.org/spec/1.2/spec.html#id2804923
    :param name: name of the input to get
    :param options: See InputOptions.
    """
    true_value = {"true", "True", "TRUE"}
    false_value = {"false", "False", "FALSE"}

    value = get_input(name, **options)
    if value in true_value:
        return True
    if value in false_value:
        return False

    raise TypeError(
        f'Input does not meet YAML 1.2 "Core Schema" specification: {name}\n'
        "Support boolean input list: `true | True | TRUE | false | False | FALSE`"
    )


def set_output(name: str, value: typing.Any) -> None:
    """
    Sets the value of an output.
    :param name: name of the output to set
    :param value: value to store. Non-string values will be converted to a
                  string via json.dumps
    """
    file_path = os.getenv("GITHUB_OUTPUT")
    if file_path:
        return issue_file_command("OUTPUT", prepare_key_value_message(name, value))

    sys.stdout.write(os.linesep)
    issue_command("set-output", {"name": name}, to_command_value(value))


def set_command_echo(enabled: bool) -> None:
    """
    Enables or disables the echoing of commands into stdout for the rest of the step.
    Echoing is disabled by default if ACTIONS_STEP_DEBUG is not set.
    """
    issue("echo", "on" if enabled else "off")


def set_failed(message: typing.Union[str, Exception]) -> None:
    """
    Sets the action status to failed.
    When the action exits it will be with an exit code of 1
    :param message: add error issue message
    """
    from actions.core import _process

    _process.CURRENT_EXIT_CODE = ExitCode.FAILURE
    error(message)


def is_debug() -> bool:
    """
    Gets whether Actions Step Debug is on or not
    """
    return os.getenv("RUNNER_DEBUG") == "1"


def debug(message: str) -> None:
    """
    Writes debug message to user log
    :param message: debug message
    """
    issue_command("debug", {}, message)


def error(
    message: typing.Union[str, Exception],
    properties: typing.Optional[AnnotationProperties] = None,
) -> None:
    """
    Adds an error issue
    :param message: error issue message. Errors will be converted to string via str()
    :param properties: optional properties to add to the annotation.
    """
    issue_command(
        "error",
        to_command_properties(properties or {}),
        str(message) if isinstance(message, Exception) else message,
    )


def warning(
    message: typing.Union[str, Exception],
    properties: typing.Optional[AnnotationProperties] = None,
) -> None:
    """
    Adds a warning issue
    :param message: warning issue message. Errors will be converted to string via str()
    :param properties: optional properties to add to the annotation.
    """
    issue_command(
        "warning",
        to_command_properties(properties or {}),
        str(message) if isinstance(message, Exception) else message,
    )


def notice(
    message: typing.Union[str, Exception],
    properties: typing.Optional[AnnotationProperties] = None,
) -> None:
    """
    Adds a notice issue
    :param message: notice issue message. Errors will be converted to string via str()
    :param properties: optional properties to add to the annotation.
    """
    issue_command(
        "notice",
        to_command_properties(properties or {}),
        str(message) if isinstance(message, Exception) else message,
    )


def info(message: str) -> None:
    """
    Writes info to log with sys.stdout.write.
    :param message: info message
    """
    sys.stdout.write(message + os.linesep)


def start_group(name: str) -> None:
    """
    Begin an output group.

    Output until the next `groupEnd` will be foldable in this group
    :param name: The name of the output group
    """
    issue("group", name)


def end_group() -> None:
    """
    End an output group.
    """
    issue("endgroup")


async def group(
    name: str,
    fn: typing.Callable[
        ..., typing.Union[typing.Coroutine[typing.Any, typing.Any, T], T]
    ],
) -> T:
    """
    Wrap a function call in a group.

    Returns the same type as the function itself.
    :param name: The name of the group
    :param fn: The function to wrap in the group
    """
    start_group(name)
    try:
        result: typing.Any = fn()
        if asyncio.iscoroutine(result):
            result = await result
    finally:
        end_group()
    return result


def save_state(name: str, value: typing.Any) -> None:
    """
    Saves state for current action, the state can only be retrieved by this
    action's post job execution.
    :param name: name of the state to store
    :param value: value to store. Non-string values will be converted to a
                  string via json.dumps
    """
    file_path = os.getenv("GITHUB_STATE")
    if file_path:
        return issue_file_command("STATE", prepare_key_value_message(name, value))

    issue_command("save-state", {"name": name}, to_command_value(value))


def get_state(name: str) -> str:
    """
    Gets the value of an state set by this action's main execution.
    :param name: name of the state to get
    """
    return os.getenv(f"STATE_{name}", "")


async def get_id_token(aud: typing.Optional[str] = None) -> str:
    return await OidcClient.get_id_token(aud)
