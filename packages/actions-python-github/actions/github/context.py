import os
import sys
import typing
from pathlib import Path

from pydantic import BaseModel, TypeAdapter

from actions.github.interfaces import WebhookPayload


class Issue(BaseModel):
    owner: str
    repo: str
    number: typing.Optional[int]


class Repo(BaseModel):
    owner: str
    repo: str


class Context(BaseModel):
    """
    Webhook payload object that triggered the workflow
    """

    payload: WebhookPayload

    event_name: str
    sha: str
    ref: str
    workflow: str
    action: str
    actor: str
    job: str
    run_number: int
    run_id: int
    api_url: str
    server_url: str
    graphql_url: str

    @classmethod
    def new(cls) -> "Context":
        """
        Hydrate the context from the environment
        """
        payload = WebhookPayload()
        github_event_path = os.getenv("GITHUB_EVENT_PATH")

        if github_event_path:
            if os.path.exists(github_event_path):
                payload = TypeAdapter(WebhookPayload).validate_json(
                    Path(github_event_path).read_bytes()
                )
            else:
                sys.stdout.write(
                    f"GITHUB_EVENT_PATH {github_event_path} does not exist{os.linesep}"
                )

        return Context(
            payload=payload,
            event_name=os.getenv("GITHUB_EVENT_NAME", ""),
            sha=os.getenv("GITHUB_SHA", ""),
            ref=os.getenv("GITHUB_REF", ""),
            workflow=os.getenv("GITHUB_WORKFLOW", ""),
            action=os.getenv("GITHUB_ACTION", ""),
            actor=os.getenv("GITHUB_ACTOR", ""),
            job=os.getenv("GITHUB_JOB", ""),
            run_number=int(os.getenv("GITHUB_RUN_NUMBER", "0")),
            run_id=int(os.getenv("GITHUB_RUN_ID", "0")),
            api_url=os.getenv("GITHUB_API_URL", "https://api.github.com"),
            server_url=os.getenv("GITHUB_API_URL", "https://github.com"),
            graphql_url=os.getenv(
                "GITHUB_GRAPHQL_URL", "https://api.github.com/graphql"
            ),
        )

    @property
    def issue(self) -> Issue:
        payload = self.payload
        repo = self.repo

        return Issue(
            owner=repo.owner,
            repo=repo.repo,
            number=(payload.issue or payload.pull_request or payload).number,
        )

    @property
    def repo(self) -> Repo:
        if os.getenv("GITHUB_REPOSITORY"):
            owner, repo = os.getenv("GITHUB_REPOSITORY", "").split("/")
            return Repo(owner=owner, repo=repo)

        if self.payload.repository:
            return Repo(
                owner=self.payload.repository.owner.login,
                repo=self.payload.repository.name,
            )

        raise Exception(
            "context.repo requires a GITHUB_REPOSITORY environment variable "
            "like 'owner/repo'"
        )
