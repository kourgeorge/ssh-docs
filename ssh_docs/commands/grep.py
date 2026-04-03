"""GREP command implementation."""

from __future__ import annotations

from .base import BaseCommand
from .path_utils import PathResolver


class GrepCommand(BaseCommand):
    """Search file contents command."""
    
    name = "grep"
    description = "Search file contents"
    
    async def execute(self, args: list[str]) -> None:
        """Execute grep command."""
        recursive = False
        filtered: list[str] = []
        
        for arg in args:
            if arg == "-R":
                recursive = True
            else:
                filtered.append(arg)
        
        if len(filtered) < 2:
            self.write_output("grep: usage: grep [-R] <pattern> <path>\n")
            return
        
        pattern = filtered[0]
        resolver = PathResolver(self.context.content_root)
        
        start_virtual = resolver.resolve_virtual_path(filtered[1], self.context.cwd)
        start_real = resolver.to_real_path(start_virtual)
        
        if start_virtual == "/invalid" or start_real is None or not start_real.exists():
            self.write_output(f"grep: no such file or directory: {start_virtual}\n")
            return
        
        if start_real.is_dir() and not recursive:
            self.write_output("grep: path is a directory, use -R\n")
            return
        
        targets = (
            [start_real]
            if start_real.is_file()
            else sorted(p for p in start_real.rglob("*") if p.is_file())
        )
        
        found = False
        for target in targets:
            try:
                lines = target.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            
            for index, line in enumerate(lines, start=1):
                if pattern.lower() in line.lower():
                    found = True
                    self.write_output(
                        f"{resolver.to_virtual_path(target)}:{index}:{line}\n"
                    )
        
        if not found:
            self.write_output("grep: no matches\n")
