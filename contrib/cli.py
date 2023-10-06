import os
import subprocess
import sys
import typing
from pathlib import Path

import rich
import typer

app = typer.Typer()

workspaces = typer.Typer()
app.add_typer(workspaces, name="workspaces")


@app.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    help="Run a command in a specified workspace",
)
def workspace(
    workspace_name: str,
    arguments: typing.List[str],
) -> None:
    code = run_in_workspace(workspace_name, arguments)
    raise typer.Exit(code=code)


@workspaces.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    help="Run a command for all workspaces",
)
def foreach(
    arguments: typing.List[str],
) -> None:
    code = 0
    for workspace in get_workspaces():
        exit_code = run_in_workspace(workspace, arguments)
        sys.stdout.write(os.linesep)
        code = exit_code if exit_code != 0 else code

    raise typer.Exit(code=code)


@workspaces.command(name="list", help="List all available workspaces")
def list_() -> None:
    for package in get_workspaces():
        rich.print(f"[blue]➤[/blue] {package}")


def get_workspaces():
    root_dir = Path(__file__).parent.parent
    for workspace_dir in Path(f"{root_dir}/packages").iterdir():
        if Path(f"{workspace_dir}/pyproject.toml").exists():
            yield workspace_dir.name


def get_workspace_dir(workspace_name: str) -> str:
    return str(Path(__file__).parent.parent / f"packages/{workspace_name}")


def run_in_workspace(workspace_name: str, arguments: typing.List[str]) -> int:
    workspace_dir = get_workspace_dir(workspace_name)

    if not Path(f"{workspace_dir}/pyproject.toml").exists():
        rich.print(f"[red]➤[/red] {workspace_name} not found")
        return 1

    rich.print(f"[blue]➤[/blue] {workspace_name}\n")
    process = subprocess.run(["rye", *arguments], cwd=workspace_dir)
    return process.returncode


if __name__ == "__main__":
    app(prog_name="rye run")
