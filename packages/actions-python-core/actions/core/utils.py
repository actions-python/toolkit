import json
import typing

if typing.TYPE_CHECKING:
    from actions.core.command import CommandProperties
    from actions.core.core import AnnotationProperties


def to_command_value(input_value: typing.Any) -> str:
    """
    Sanitizes an input into a string so it can be passed into issueCommand safely
    :param input_value: input to sanitize into a string
    :return: string
    """
    if input_value is None:
        return ""
    elif isinstance(input_value, str):
        return input_value
    else:
        return json.dumps(input_value)


def to_command_properties(
    annotation_properties: "AnnotationProperties"
) -> "CommandProperties":
    if len(annotation_properties) == 0:
        return {}

    return {
        "title": annotation_properties.get("title"),
        "file": annotation_properties.get("file"),
        "line": annotation_properties.get("start_line"),
        "endLine": annotation_properties.get("end_line"),
        "col": annotation_properties.get("start_column"),
        "endColumn": annotation_properties.get("end_column"),
    }
