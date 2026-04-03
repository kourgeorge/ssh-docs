"""SSH-Docs shell commands package.

This package provides a modular command architecture for the SSH-Docs shell.
Each command is implemented as a separate class inheriting from BaseCommand.
"""

from .base import BaseCommand, ShellContext
from .cat import CatCommand
from .cd import CdCommand
from .find import FindCommand
from .grep import GrepCommand
from .head_tail import HeadCommand, TailCommand
from .help import HelpCommand
from .ls import LsCommand
from .path_utils import PathResolver
from .pwd import PwdCommand
from .registry import CommandRegistry

__all__ = [
    "BaseCommand",
    "ShellContext",
    "CommandRegistry",
    "PathResolver",
    "CatCommand",
    "CdCommand",
    "FindCommand",
    "GrepCommand",
    "HeadCommand",
    "TailCommand",
    "HelpCommand",
    "LsCommand",
    "PwdCommand",
]
