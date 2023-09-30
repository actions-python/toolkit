import os
import typing

import githubkit
import githubkit.config

from actions import core
from actions.github.context import Context

context = Context.new()


def get_githubkit(
    token: typing.Optional[str] = None, config: typing.Optional[githubkit.Config] = None
) -> githubkit.GitHub:
    """
    Returns a hydrated githubkit ready to use for GitHub Actions
    :params token: the repo PAT or GITHUB_TOKEN
    :params options: other options to set
    """
    return githubkit.GitHub(
        auth=(
            token
            or os.getenv("GITHUB_TOKEN")
            or core.get_input("github-token")
            or core.get_input("token")
            or None
        ),
        **{
            **(config.dict() if config else {}),
            "base_url": context.server_url,
        },
    )
