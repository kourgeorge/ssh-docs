"""LS command implementation."""

from __future__ import annotations

from .base import BaseCommand
from .path_utils import PathResolver


class LsCommand(BaseCommand):
    """List directory contents command."""
    
    name = "ls"
    description = "List directory contents"
    
    async def execute(self, args: list[str]) -> None:
        """Execute ls command."""
        resolver = PathResolver(self.context.content_root)
        
        virtual_path = resolver.resolve_virtual_path(
            args[0] if args else None,
            self.context.cwd
        )
        real_path = resolver.to_real_path(virtual_path)
        
        if virtual_path == "/invalid" or real_path is None or not real_path.exists():
            self.write_output(f"ls: no such file or directory: {virtual_path}\n")
            return
        
        if real_path.is_file():
            self.write_output(f"{real_path.name}\n")
            return
        
        for child in sorted(
            real_path.iterdir(),
            key=lambda p: (not p.is_dir(), p.name.lower())
        ):
            self.write_output(f"{child.name}\n")
