"""FIND command implementation."""

from __future__ import annotations

import re

from .base import BaseCommand
from .path_utils import PathResolver


class FindCommand(BaseCommand):
    """Find files matching criteria command."""
    
    name = "find"
    description = "Find files matching criteria"
    
    async def execute(self, args: list[str]) -> None:
        """Execute find command."""
        resolver = PathResolver(self.context.content_root)
        
        start_virtual = resolver.resolve_virtual_path(
            args[0] if args else self.context.cwd,
            self.context.cwd
        )
        start_real = resolver.to_real_path(start_virtual)
        
        if start_virtual == "/invalid" or start_real is None or not start_real.exists():
            self.write_output(f"find: no such file or directory: {start_virtual}\n")
            return
        
        name_filter = None
        if len(args) >= 3 and args[1] == "-name":
            name_filter = args[2]
        
        paths = (
            [start_real]
            if start_real.is_file()
            else [start_real, *sorted(start_real.rglob("*"))]
        )
        
        for path in paths:
            if name_filter and not self._matches_name(path.name, name_filter):
                continue
            self.write_output(f"{resolver.to_virtual_path(path)}\n")
    
    def _matches_name(self, name: str, pattern: str) -> bool:
        """Check if filename matches glob pattern."""
        regex = "^" + re.escape(pattern).replace(r"\*", ".*") + "$"
        return re.match(regex, name) is not None
