import os


def to_posix_path(path: str) -> str:
    """
    to_posix_path converts the given path to the posix form. On Windows, \\\\
    will be replaced with /.
    :params pth: Path to transform.
    :return: Posix path.
    """
    return path.replace("\\", "/")


def to_win32_path(path: str) -> str:
    """
    to_win32_path converts the given path to the win32 form. On Linux, / will be
    replaced with \\\\.
    :params pth: Path to transform.
    :return: Win32 path.
    """
    return path.replace("/", "\\")


def to_platform_path(path: str) -> str:
    """
    to_platform_path converts the given path to a platform-specific path. It
    does this by replacing instances of / and \\ with the platform-specific path
    separator.
    :params pth: The path to platformize.
    :return: The platform-specific path.
    """
    return path.replace("/", os.sep).replace("\\", os.sep)
