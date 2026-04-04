"""File system abstraction layer for SSH-Docs.

Provides a clean interface for file system operations, enabling:
- Easy testing through mocking
- Potential for different backends (local, remote, virtual)
- Centralized error handling
- Performance optimizations (caching, async I/O)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator, Optional


class FileSystemService(ABC):
    """Abstract interface for file system operations.
    
    This abstraction allows commands to work with files without
    directly depending on the file system implementation.
    """
    
    @abstractmethod
    def exists(self, path: Path) -> bool:
        """Check if a path exists.
        
        Args:
            path: Path to check
            
        Returns:
            True if path exists, False otherwise
        """
        pass
    
    @abstractmethod
    def is_file(self, path: Path) -> bool:
        """Check if path is a file.
        
        Args:
            path: Path to check
            
        Returns:
            True if path is a file, False otherwise
        """
        pass
    
    @abstractmethod
    def is_dir(self, path: Path) -> bool:
        """Check if path is a directory.
        
        Args:
            path: Path to check
            
        Returns:
            True if path is a directory, False otherwise
        """
        pass
    
    @abstractmethod
    def read_text(self, path: Path, encoding: str = "utf-8") -> str:
        """Read text content from a file.
        
        Args:
            path: Path to file
            encoding: Text encoding to use
            
        Returns:
            File content as string
            
        Raises:
            FileNotFoundError: If file doesn't exist
            UnicodeDecodeError: If file is not valid text
            PermissionError: If file cannot be read
        """
        pass
    
    @abstractmethod
    def list_dir(self, path: Path) -> Iterator[Path]:
        """List directory contents.
        
        Args:
            path: Path to directory
            
        Returns:
            Iterator of paths in the directory
            
        Raises:
            FileNotFoundError: If directory doesn't exist
            NotADirectoryError: If path is not a directory
            PermissionError: If directory cannot be read
        """
        pass
    
    @abstractmethod
    def glob(self, path: Path, pattern: str) -> Iterator[Path]:
        """Find files matching a glob pattern.
        
        Args:
            path: Base path to search from
            pattern: Glob pattern (e.g., "*.txt", "**/*.py")
            
        Returns:
            Iterator of matching paths
        """
        pass


class VirtualFileSystem(FileSystemService):
    """Virtual file system with injected files.
    
    Wraps a real filesystem but adds virtual files at the root level.
    Used to inject AGENTS.md, SETUP.md, and SKILL.md files.
    """
    
    def __init__(self, backend: FileSystemService, virtual_files: dict[str, str], content_root: Path) -> None:
        """Initialize virtual file system.
        
        Args:
            backend: Underlying file system service
            virtual_files: Dict mapping virtual filenames to their content
            content_root: The content root directory path
        """
        self.backend = backend
        self.virtual_files = virtual_files
        self.content_root = content_root.resolve()
    
    def _is_virtual_file(self, path: Path) -> bool:
        """Check if path refers to a virtual file at content root."""
        return path.name in self.virtual_files and path.parent == self.content_root
    
    def exists(self, path: Path) -> bool:
        """Check if a path exists (including virtual files)."""
        if self._is_virtual_file(path):
            return True
        return self.backend.exists(path)
    
    def is_file(self, path: Path) -> bool:
        """Check if path is a file (including virtual files)."""
        if self._is_virtual_file(path):
            return True
        return self.backend.is_file(path)
    
    def is_dir(self, path: Path) -> bool:
        """Check if path is a directory."""
        if self._is_virtual_file(path):
            return False
        return self.backend.is_dir(path)
    
    def read_text(self, path: Path, encoding: str = "utf-8") -> str:
        """Read text content from a file (including virtual files)."""
        if self._is_virtual_file(path):
            return self.virtual_files[path.name]
        return self.backend.read_text(path, encoding)
    
    def list_dir(self, path: Path) -> Iterator[Path]:
        """List directory contents (including virtual files at root)."""
        items = list(self.backend.list_dir(path))
        
        # Add virtual files if listing content root directory
        if path.resolve() == self.content_root:
            for filename in self.virtual_files.keys():
                virtual_path = path / filename
                items.append(virtual_path)
        
        return iter(items)
    
    def glob(self, path: Path, pattern: str) -> Iterator[Path]:
        """Find files matching a glob pattern."""
        return self.backend.glob(path, pattern)


class LocalFileSystem(FileSystemService):
    """Local file system implementation.
    
    Provides direct access to the local file system using pathlib.
    This is the default implementation for production use.
    """
    
    def exists(self, path: Path) -> bool:
        """Check if a path exists."""
        return path.exists()
    
    def is_file(self, path: Path) -> bool:
        """Check if path is a file."""
        return path.is_file()
    
    def is_dir(self, path: Path) -> bool:
        """Check if path is a directory."""
        return path.is_dir()
    
    def read_text(self, path: Path, encoding: str = "utf-8") -> str:
        """Read text content from a file."""
        return path.read_text(encoding=encoding)
    
    def list_dir(self, path: Path) -> Iterator[Path]:
        """List directory contents."""
        return path.iterdir()
    
    def glob(self, path: Path, pattern: str) -> Iterator[Path]:
        """Find files matching a glob pattern."""
        return path.glob(pattern)


class CachedFileSystem(FileSystemService):
    """Cached file system wrapper.
    
    Wraps another FileSystemService and adds caching for:
    - File existence checks
    - Directory listings
    - File content (with size limits)
    
    This improves performance for repeated operations on the same files.
    """
    
    def __init__(self, backend: FileSystemService, cache_size: int = 128) -> None:
        """Initialize cached file system.
        
        Args:
            backend: Underlying file system service
            cache_size: Maximum number of items to cache
        """
        self.backend = backend
        self.cache_size = cache_size
        self._exists_cache: dict[Path, bool] = {}
        self._is_file_cache: dict[Path, bool] = {}
        self._is_dir_cache: dict[Path, bool] = {}
        self._content_cache: dict[Path, str] = {}
    
    def exists(self, path: Path) -> bool:
        """Check if a path exists (cached)."""
        if path not in self._exists_cache:
            if len(self._exists_cache) >= self.cache_size:
                # Simple FIFO eviction
                self._exists_cache.pop(next(iter(self._exists_cache)))
            self._exists_cache[path] = self.backend.exists(path)
        return self._exists_cache[path]
    
    def is_file(self, path: Path) -> bool:
        """Check if path is a file (cached)."""
        if path not in self._is_file_cache:
            if len(self._is_file_cache) >= self.cache_size:
                self._is_file_cache.pop(next(iter(self._is_file_cache)))
            self._is_file_cache[path] = self.backend.is_file(path)
        return self._is_file_cache[path]
    
    def is_dir(self, path: Path) -> bool:
        """Check if path is a directory (cached)."""
        if path not in self._is_dir_cache:
            if len(self._is_dir_cache) >= self.cache_size:
                self._is_dir_cache.pop(next(iter(self._is_dir_cache)))
            self._is_dir_cache[path] = self.backend.is_dir(path)
        return self._is_dir_cache[path]
    
    def read_text(self, path: Path, encoding: str = "utf-8") -> str:
        """Read text content from a file (cached for small files)."""
        cache_key = path
        if cache_key not in self._content_cache:
            content = self.backend.read_text(path, encoding)
            # Only cache files smaller than 100KB
            if len(content) < 100_000:
                if len(self._content_cache) >= self.cache_size:
                    self._content_cache.pop(next(iter(self._content_cache)))
                self._content_cache[cache_key] = content
            return content
        return self._content_cache[cache_key]
    
    def list_dir(self, path: Path) -> Iterator[Path]:
        """List directory contents (not cached - returns iterator)."""
        return self.backend.list_dir(path)
    
    def glob(self, path: Path, pattern: str) -> Iterator[Path]:
        """Find files matching a glob pattern (not cached - returns iterator)."""
        return self.backend.glob(path, pattern)
    
    def clear_cache(self) -> None:
        """Clear all caches."""
        self._exists_cache.clear()
        self._is_file_cache.clear()
        self._is_dir_cache.clear()
        self._content_cache.clear()
