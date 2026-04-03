"""Base command abstraction for SSH-Docs shell commands."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..filesystem import FileSystemService


class BaseCommand(ABC):
    """Abstract base class for all shell commands.
    
    Provides common functionality and enforces a consistent interface
    for command implementations.
    
    Subclasses must define class attributes:
        name: str - The command name (e.g., 'ls', 'cd')
        description: str - Brief description of what the command does
    """
    
    # Class attributes that must be overridden by subclasses
    name: str = ""
    description: str = ""
    
    def __init__(self, shell_context: ShellContext) -> None:
        """Initialize command with shell context.
        
        Args:
            shell_context: The shell context providing access to state and I/O
        """
        self.context = shell_context
        
        # Validate that subclass defined required attributes
        if not self.name:
            raise ValueError(f"{self.__class__.__name__} must define 'name' class attribute")
        if not self.description:
            raise ValueError(f"{self.__class__.__name__} must define 'description' class attribute")
    
    @abstractmethod
    async def execute(self, args: list[str]) -> None:
        """Execute the command with given arguments.
        
        Args:
            args: List of command arguments (excluding the command name itself)
        """
        pass
    
    def write_output(self, message: str) -> None:
        """Write output to stdout.
        
        Args:
            message: The message to write
        """
        self.context.stdout.write(message)
    
    def write_error(self, message: str) -> None:
        """Write error message to stderr.
        
        Args:
            message: The error message to write
        """
        self.context.stderr.write(message)


class ShellContext:
    """Context object providing shell state and I/O to commands.
    
    This decouples commands from the shell implementation, allowing
    commands to access only what they need.
    """
    
    def __init__(
        self,
        stdout: Any,
        stderr: Any,
        content_root: Path,
        site_name: str,
        filesystem: Optional[FileSystemService] = None,
        cwd: str = "/site",
    ) -> None:
        """Initialize shell context.
        
        Args:
            stdout: Standard output stream
            stderr: Standard error stream
            content_root: Root directory of the documentation content
            site_name: Name of the documentation site
            filesystem: File system service (defaults to LocalFileSystem)
            cwd: Current working directory (virtual path)
        """
        self.stdout = stdout
        self.stderr = stderr
        self.content_root = content_root.resolve()
        self.site_name = site_name
        self._cwd = cwd
        
        # Use provided filesystem or create default
        if filesystem is None:
            from ..filesystem import LocalFileSystem
            filesystem = LocalFileSystem()
        self.filesystem = filesystem
    
    @property
    def cwd(self) -> str:
        """Get current working directory."""
        return self._cwd
    
    @cwd.setter
    def cwd(self, value: str) -> None:
        """Set current working directory."""
        self._cwd = value
