"""HELP command implementation."""

from __future__ import annotations

from .base import BaseCommand


class HelpCommand(BaseCommand):
    """Display available commands."""
    
    name = "help"
    description = "Display available commands"
    
    async def execute(self, args: list[str]) -> None:
        """Execute help command."""
        self.write_output(
            "Commands: pwd, ls, cd, cat, head, tail, find, grep, help, exit\n"
        )
