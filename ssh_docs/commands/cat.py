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
        file_path = self._require_file_arg(args)
        if file_path is None:
            return
        
        try:
            content = file_path.read_text(encoding="utf-8")
            self.write_output(content.rstrip() + "\n")
        except UnicodeDecodeError:
            self.write_output("cat: cannot read binary file\n")
    
    def _require_file_arg(self, args: list[str]) -> Optional[Path]:
        """Validate and return file path from arguments."""
        if not args:
            self.write_output("cat: missing file operand\n")
            return None
        
        resolver = PathResolver(self.context.content_root)
        virtual_path = resolver.resolve_virtual_path(args[0], self.context.cwd)
        real_path = resolver.to_real_path(virtual_path)
        
        if virtual_path == "/invalid" or real_path is None or not real_path.exists():
            self.write_output(f"cat: no such file: {virtual_path}\n")
            return None
        
        if not real_path.is_file():
            self.write_output(f"cat: is a directory: {virtual_path}\n")
            return None
        
        return real_path
