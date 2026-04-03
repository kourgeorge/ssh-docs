"""CD command implementation."""

from __future__ import annotations

from .base import BaseCommand
from .path_utils import PathResolver


class CdCommand(BaseCommand):
    """Change directory command."""
    
    name = "cd"
    description = "Change current directory"
    
    async def execute(self, args: list[str]) -> None:
        """Execute cd command."""
        resolver = PathResolver(self.context.content_root)
        
        virtual_path = resolver.resolve_virtual_path(
            args[0] if args else "/site",
            self.context.cwd
        )
        real_path = resolver.to_real_path(virtual_path)
        
        if virtual_path == "/invalid" or real_path is None or not real_path.exists():
            self.write_output(f"cd: no such file or directory: {virtual_path}\n")
            return
        
        if not real_path.is_dir():
            self.write_output(f"cd: not a directory: {virtual_path}\n")
            return
        
        self.context.cwd = virtual_path
