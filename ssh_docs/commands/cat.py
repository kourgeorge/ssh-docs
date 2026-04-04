"""CAT command implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .base import BaseCommand
from .path_utils import PathResolver


class CatCommand(BaseCommand):
    """Display file contents command."""
    
    name = "cat"
    description = "Display file contents"
    
    async def execute(self, args: list[str]) -> None:
        """Execute cat command."""
        if not args:
            self.write_output("cat: missing file operand\n")
            return
        
        resolver = PathResolver(self.context.content_root)
        virtual_path = resolver.resolve_virtual_path(args[0], self.context.cwd)
        
        # Handle virtual files at root (AGENTS.md, SETUP.md, SKILL.md)
        if virtual_path.startswith("/") and not virtual_path.startswith("/docs") and virtual_path != "/invalid":
            filename = virtual_path.lstrip("/")
            # Virtual files are stored at content_root in the virtual filesystem
            virtual_file_path = self.context.content_root / filename
            
            # Check if it exists in the virtual filesystem
            if self.context.filesystem.exists(virtual_file_path):
                if not self.context.filesystem.is_file(virtual_file_path):
                    self.write_output(f"cat: is a directory: {virtual_path}\n")
                    return
                try:
                    content = self.context.filesystem.read_text(virtual_file_path)
                    self.write_output(content.rstrip() + "\n")
                    return
                except Exception as e:
                    self.write_output(f"cat: cannot read file: {e}\n")
                    return
            else:
                self.write_output(f"cat: no such file: {virtual_path}\n")
                return
        
        # Handle /docs paths
        real_path = resolver.to_real_path(virtual_path)
        
        if virtual_path == "/invalid" or real_path is None or not self.context.filesystem.exists(real_path):
            self.write_output(f"cat: no such file: {virtual_path}\n")
            return
        
        if not self.context.filesystem.is_file(real_path):
            self.write_output(f"cat: is a directory: {virtual_path}\n")
            return
        
        try:
            content = self.context.filesystem.read_text(real_path, encoding="utf-8")
            self.write_output(content.rstrip() + "\n")
        except UnicodeDecodeError:
            self.write_output("cat: cannot read binary file\n")
