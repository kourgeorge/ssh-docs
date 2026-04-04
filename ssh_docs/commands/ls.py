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
        
        # Handle root directory listing
        if virtual_path == "/":
            # List virtual files at root
            for filename in ["AGENTS.md", "SETUP.md", "SKILL.md"]:
                self.write_output(f"{filename}\n")
            # Also list docs directory
            self.write_output("docs\n")
            return
        
        real_path = resolver.to_real_path(virtual_path)
        
        if virtual_path == "/invalid" or real_path is None or not real_path.exists():
            self.write_output(f"ls: no such file or directory: {virtual_path}\n")
            return
        
        if real_path.is_file():
            self.write_output(f"{real_path.name}\n")
            return
        
        # Use filesystem service to list directory (includes virtual files at content root)
        try:
            for child in sorted(
                self.context.filesystem.list_dir(real_path),
                key=lambda p: (not self.context.filesystem.is_dir(p), p.name.lower())
            ):
                self.write_output(f"{child.name}\n")
        except (PermissionError, OSError) as e:
            self.write_output(f"ls: cannot access: {e}\n")
