import dataclasses
import json
import os
import sys
import typing
from pathlib import Path


@dataclasses.dataclass
class Issue:
    owner: str
    repo: str
    number: typing.Optional[int]


@dataclasses.dataclass
class Repo:
    owner: str
    repo: str


class Context:
    """
    Webhook payload object that triggered the workflow
    """

    payload: dict
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

    def __init__(self):
        """
        Hydrate the context from the environment
        """
        self.payload = {}
        github_event_path = os.getenv("GITHUB_EVENT_PATH")

        if github_event_path:
            if os.path.exists(github_event_path):
                self.payload = json.loads(Path(github_event_path).read_bytes())
            else:
                sys.stdout.write(
                    f"GITHUB_EVENT_PATH {github_event_path} does not exist{os.linesep}"
                )

        self.event_name = os.getenv("GITHUB_EVENT_NAME", "")
        self.sha = os.getenv("GITHUB_SHA", "")
        self.ref = os.getenv("GITHUB_REF", "")
        self.workflow = os.getenv("GITHUB_WORKFLOW", "")
        self.action = os.getenv("GITHUB_ACTION", "")
        self.actor = os.getenv("GITHUB_ACTOR", "")
        self.job = os.getenv("GITHUB_JOB", "")
        self.run_number = int(os.getenv("GITHUB_RUN_NUMBER", "0"))
        self.run_id = int(os.getenv("GITHUB_RUN_ID", "0"))
        self.api_url = os.getenv("GITHUB_API_URL", "https://api.github.com")
        self.server_url = os.getenv("GITHUB_API_URL", "https://github.com")
        self.graphql_url = os.getenv(
            "GITHUB_GRAPHQL_URL", "https://api.github.com/graphql"
        )

    @property
    def issue(self) -> Issue:
        if "issue" in self.payload:
            number = self.payload["issue"]["number"]
        elif "pull_request" in self.payload:
            number = self.payload["pull_request"]["number"]
        else:
            number = self.payload.get("number")
        return Issue(owner=self.repo.owner, repo=self.repo.repo, number=number)

    @property
    def repo(self) -> Repo:
        if os.getenv("GITHUB_REPOSITORY"):
            owner, repo = os.getenv("GITHUB_REPOSITORY", "").split("/")
            return Repo(owner=owner, repo=repo)

        if "repository" in self.payload:
            return Repo(
                owner=self.payload["repository"]["owner"]["login"],
                repo=self.payload["repository"]["name"],
            )

        raise Exception(
            "context.repo requires a GITHUB_REPOSITORY environment variable "
            "like 'owner/repo'"
        )
