import os
import typing
import uuid

from actions.core.utils import to_command_value


def issue_file_command(command: str, message: typing.Any) -> None:
    file_path = os.getenv(f"GITHUB_{command}")
    if not file_path:
        raise Exception(
            f"Unable to find environment variable for file command {command}"
        )

    if not os.path.exists(file_path):
        raise Exception(f"Missing file at path: {file_path}")

    with open(file_path, "a", encoding="utf-8") as f:
        f.write(f"{to_command_value(message)}{os.linesep}")


def prepare_key_value_message(key: str, value: typing.Any) -> str:
    delimiter = f"ghadelimiter_{uuid.uuid4()}"
    converted_value = to_command_value(value)

    # These should realistically never happen, but just in case someone finds a
    # way to exploit uuid generation let's not allow keys or values that contain
    # the delimiter.
    if delimiter in key:
        raise Exception(
            f'Unexpected input: name should not contain the delimiter "{delimiter}"'
        )

    if delimiter in converted_value:
        raise Exception(
            f'Unexpected input: value should not contain the delimiter "{delimiter}"'
        )

    return f"{key}<<{delimiter}{os.linesep}{converted_value}{os.linesep}{delimiter}"
