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
    filter_paths: typing.Annotated[
        bool,
        typer.Option(help="A flag to filter paths from arguments for mono repository."),
    ] = False,
) -> None:
    code = run_in_workspace(workspace_name, arguments, filter_paths=filter_paths)
    raise typer.Exit(code=code)


@workspaces.command(
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    help="Run a command for all workspaces",
)
def foreach(
    arguments: typing.List[str],
    filter_paths: typing.Annotated[
        bool,
        typer.Option(help="A flag to filter paths from arguments for mono repository."),
    ] = False,
) -> None:
    code = 0
    for workspace in get_workspaces():
        exit_code = run_in_workspace(workspace, arguments, filter_paths=filter_paths)
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


def run_in_workspace(
    workspace_name: str, arguments: typing.List[str], *, filter_paths: bool
) -> int:
    workspace_dir = get_workspace_dir(workspace_name)

    if not Path(f"{workspace_dir}/pyproject.toml").exists():
        rich.print(f"[red]➤[/red] {workspace_name} not found")
        return 1

    if filter_paths:
        arguments, ok = filter_paths_from_arguments(workspace_name, arguments)
        if not ok:
            rich.print(f"[yellow]➤[/yellow] {workspace_name} no files to run")
            return 0

    rich.print(f"[blue]➤[/blue] {workspace_name}\n")
    process = subprocess.run(["hatch", *arguments], cwd=workspace_dir)
    return process.returncode


def filter_paths_from_arguments(
    workspace_name: str, arguments: typing.List[str]
) -> typing.Tuple[typing.List[str], bool]:
    ok = False
    workspace_dir = get_workspace_dir(workspace_name) + "/"
    filtered_arguments = []

    for argument in arguments[1:]:
        resolved_path = Path(argument).resolve()
        if resolved_path.exists():
            resolved = str(resolved_path)
            if resolved.startswith(workspace_dir):
                ok = True
                filtered_arguments.append(resolved.replace(workspace_dir, ""))
        else:
            filtered_arguments.append(argument)

    return [arguments[0], *filtered_arguments], ok


if __name__ == "__main__":
    app(prog_name="hatch run")
