"""HEAD and TAIL command implementations."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .base import BaseCommand
from .path_utils import PathResolver


class HeadCommand(BaseCommand):
    """Display first lines of a file command."""
    
    name = "head"
    description = "Display first lines of a file"
    
    async def execute(self, args: list[str]) -> None:
        """Execute head command."""
        await self._print_slice(args, tail=False)
    
    async def _print_slice(self, args: list[str], tail: bool) -> None:
        """Helper for head/tail commands."""
        command = "tail" if tail else "head"
        
        if not args:
            self.write_output(f"{command}: missing file operand\n")
            return
        
        count = 10
        file_index = 0
        
        if len(args) >= 2 and args[0] == "-n":
            try:
                count = int(args[1])
            except ValueError:
                self.write_output(f"{command}: invalid line count\n")
                return
            file_index = 2
        
        if file_index >= len(args):
            self.write_output(f"{command}: missing file operand\n")
            return
        
        file_path = self._require_file_arg(command, [args[file_index]])
        if file_path is None:
            return
        
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
            selected = lines[-count:] if tail else lines[:count]
            self.write_output("\n".join(selected) + "\n")
        except UnicodeDecodeError:
            self.write_output(f"{command}: cannot read binary file\n")
    
    def _require_file_arg(self, command: str, args: list[str]) -> Optional[Path]:
        """Validate and return file path from arguments."""
        if not args:
            self.write_output(f"{command}: missing file operand\n")
            return None
        
        resolver = PathResolver(self.context.content_root)
        virtual_path = resolver.resolve_virtual_path(args[0], self.context.cwd)
        real_path = resolver.to_real_path(virtual_path)
        
        if virtual_path == "/invalid" or real_path is None or not real_path.exists():
            self.write_output(f"{command}: no such file: {virtual_path}\n")
            return None
        
        if not real_path.is_file():
            self.write_output(f"{command}: is a directory: {virtual_path}\n")
            return None
        
        return real_path


class TailCommand(HeadCommand):
    """Display last lines of a file command."""
    
    name = "tail"
    description = "Display last lines of a file"
    
    async def execute(self, args: list[str]) -> None:
        """Execute tail command."""
        await self._print_slice(args, tail=True)
