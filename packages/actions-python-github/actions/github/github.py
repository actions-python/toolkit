import os
import typing

from actions import core
from actions.github.context import Context

context = Context()


def get_github(token: typing.Optional[str] = None, **config):
    """
    Returns a hydrated pygithub ready to use for GitHub Actions
    :params token: the repo PAT or GITHUB_TOKEN
    :params config: other options to set
    """
    import github
    import github.Auth

    token = (
        token
        or os.getenv("GITHUB_TOKEN")
        or core.get_input("github-token")
        or core.get_input("token")
    )

    return github.Github(  # type: ignore[attr-defined]
        **{
            "auth": github.Auth.Token(token) if token else None,
            "base_url": context.api_url,
            **config,
        },
    )


def get_githubkit(token: typing.Optional[str] = None, **config):
    """
    Returns a hydrated githubkit ready to use for GitHub Actions
    :params token: the repo PAT or GITHUB_TOKEN
    :params config: other options to set
    """
    import githubkit

    return githubkit.GitHub(
        **{
            "auth": (
                token
                or os.getenv("GITHUB_TOKEN")
                or core.get_input("github-token")
                or core.get_input("token")
                or None
            ),
            "base_url": context.api_url,
            **config,
        },
    )
