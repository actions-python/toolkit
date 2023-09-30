import os
import sys
import typing

from actions.core.utils import to_command_value

CommandProperties = typing.Dict[str, typing.Any]


def issue_command(
    command: str, properties: CommandProperties, message: typing.Any
) -> None:
    """
    Commands

    Command Format:
        ::name key=value,key=value::message

    Examples:
        ::warning::This is the message
        ::set-env name=MY_VAR::some value
    """
    cmd = Command(command, properties, message)
    sys.stdout.write(str(cmd) + os.linesep)


def issue(name: str, message: str = "") -> None:
    issue_command(name, {}, message)


CMD_STRING = "::"


class Command:
    command: str
    message: str
    properties: CommandProperties

    def __init__(
        self, command: str, properties: CommandProperties, message: str
    ) -> None:
        self.command = command or "missing.command"
        self.properties = properties
        self.message = message

    def __str__(self) -> str:
        cmd_str = CMD_STRING + self.command

        if self.properties and len(self.properties) > 0:
            cmd_str += " "
            cmd_str += ",".join(
                [
                    f"{k}={escape_property(v)}"
                    for k, v in self.properties.items()
                    if v is not None
                ]
            )

        cmd_str += f"{CMD_STRING}{escape_data(self.message)}"
        return cmd_str


def escape_data(s: typing.Any) -> str:
    return (
        to_command_value(s)
        .replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
    )


def escape_property(s: typing.Any) -> str:
    return (
        to_command_value(s)
        .replace("%", "%25")
        .replace("\r", "%0D")
        .replace("\n", "%0A")
        .replace(":", "%3A")
        .replace(",", "%2C")
    )
