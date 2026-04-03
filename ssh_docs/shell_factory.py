"""Shell factory for dependency injection.

Provides a clean way to create shell instances with proper dependencies,
enabling easier testing and configuration.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Protocol

from .filesystem import FileSystemService, LocalFileSystem


class ShellFactory(Protocol):
    """Protocol for shell factories.
    
    This allows different shell implementations to be injected
    into the server without tight coupling.
    """
    
    def create_shell(
        self,
        input_queue: Any,
        stdout: Any,
        stderr: Any,
    ) -> Any:
        """Create a shell instance.
        
        Args:
            input_queue: Async queue for reading user input
            stdout: Standard output stream
            stderr: Standard error stream
            
        Returns:
            Shell instance
        """
        ...


class DefaultShellFactory:
    """Default factory for creating SSH-Docs shells.
    
    This factory encapsulates all the dependencies needed to create
    a shell instance, making it easy to configure and test.
    """
    
    def __init__(
        self,
        content_root: Path,
        site_name: str,
        banner: Optional[str] = None,
        filesystem: Optional[FileSystemService] = None,
    ) -> None:
        """Initialize shell factory.
        
        Args:
            content_root: Root directory of the documentation content
            site_name: Name of the documentation site
            banner: Optional custom banner message
            filesystem: File system service (defaults to LocalFileSystem)
        """
        self.content_root = content_root
        self.site_name = site_name
        self.banner = banner
        self.filesystem = filesystem or LocalFileSystem()
    
    def create_shell(
        self,
        input_queue: Any,
        stdout: Any,
        stderr: Any,
    ) -> Any:
        """Create a shell instance with configured dependencies.
        
        Args:
            input_queue: Async queue for reading user input
            stdout: Standard output stream
            stderr: Standard error stream
            
        Returns:
            SSHDocsShell instance
        """
        from .shell import SSHDocsShell
        
        return SSHDocsShell(
            input_queue=input_queue,
            stdout=stdout,
            stderr=stderr,
            content_root=self.content_root,
            site_name=self.site_name,
            banner=self.banner,
            filesystem=self.filesystem,
        )
