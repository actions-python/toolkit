import typing

from pydantic import BaseModel


class Owner(BaseModel):
    login: str
    name: typing.Optional[str] = None


class PayloadRepository(BaseModel):
    full_name: typing.Optional[str] = None
    name: str
    owner: Owner
    html_url: typing.Optional[str] = None


class Issue(BaseModel):
    number: int
    html_url: typing.Optional[str] = None
    body: typing.Optional[str] = None


class PullRequest(BaseModel):
    number: int
    html_url: typing.Optional[str] = None
    body: typing.Optional[str] = None


class Sender(BaseModel):
    type: str


class Installation(BaseModel):
    id: int


class Comment(BaseModel):
    id: int


class WebhookPayload(BaseModel):
    number: typing.Optional[int] = None
    repository: typing.Optional[PayloadRepository] = None
    issue: typing.Optional[Issue] = None
    pull_request: typing.Optional[PullRequest] = None
    sender: typing.Optional[Sender] = None
    action: typing.Optional[str] = None
    installation: typing.Optional[Installation] = None
    comment: typing.Optional[Comment] = None
