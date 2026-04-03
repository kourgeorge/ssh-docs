"""PWD command implementation."""

from __future__ import annotations

from .base import BaseCommand


class PwdCommand(BaseCommand):
    """Print working directory command."""
    
    name = "pwd"
    description = "Print current working directory"
    
    async def execute(self, args: list[str]) -> None:
        """Execute pwd command."""
        self.write_output(f"{self.context.cwd}\n")
