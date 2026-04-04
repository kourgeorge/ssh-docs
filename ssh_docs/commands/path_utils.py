"""Path resolution utilities for SSH-Docs shell.

Provides secure path resolution between virtual paths (/docs/...) and
real filesystem paths, with security checks to prevent directory traversal.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


class PathResolver:
    """Handles conversion between virtual and real paths with security checks."""
    
    def __init__(self, content_root: Path) -> None:
        """Initialize path resolver.
        
        Args:
            content_root: Root directory of the documentation content
        """
        self.content_root = content_root.resolve()
    
    def resolve_virtual_path(self, value: Optional[str], cwd: str) -> str:
        """Resolve a path argument to a normalized virtual path.
        
        Args:
            value: Path to resolve (can be absolute or relative)
            cwd: Current working directory (virtual path)
            
        Returns:
            Normalized virtual path starting with / or /docs
        """
        if not value:
            return cwd
        
        candidate = value if value.startswith("/") else str(Path(cwd) / value)
        normalized = os.path.normpath(candidate).replace("\\", "/")
        
        # Allow root directory
        if normalized == "/":
            return "/"
        
        # Allow root-level files (for virtual files like AGENTS.md, SETUP.md, SKILL.md)
        if normalized.startswith("/") and "/" not in normalized[1:]:
            return normalized
        
        # Must start with /docs for content paths
        if not normalized.startswith("/docs"):
            return "/invalid"
        
        return normalized
    
    def to_real_path(self, virtual_path: str) -> Optional[Path]:
        """Convert virtual path to real filesystem path with security checks.
        
        Performs multiple security validations:
        1. Ensures path starts with /docs prefix
        2. Resolves symlinks and checks final target is within content_root
        3. Validates that symlinks don't escape the content root
        
        Args:
            virtual_path: Virtual path starting with /docs
            
        Returns:
            Real filesystem path if valid, None if security check fails
        """
        if not virtual_path.startswith("/docs"):
            return None
        
        rel = virtual_path.removeprefix("/docs").lstrip("/")
        candidate = self.content_root / rel
        
        # Check if the path itself (before resolving) tries to escape
        try:
            candidate.relative_to(self.content_root)
        except ValueError:
            # Path construction itself is trying to escape
            return None
        
        # Resolve symlinks to get the actual target
        target = candidate.resolve()
        
        # Verify the resolved target is still within content_root
        try:
            target.relative_to(self.content_root)
        except ValueError:
            # Symlink points outside content_root - security violation
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                f"Blocked access to symlink escape: {virtual_path} -> {target}"
            )
            return None
        
        return target
    
    def to_virtual_path(self, path: Path) -> str:
        """Convert real filesystem path to virtual path.
        
        Args:
            path: Real filesystem path
            
        Returns:
            Virtual path starting with /docs
        """
        rel = path.relative_to(self.content_root)
        rel_str = str(rel).replace("\\", "/")
        return "/docs" if rel_str == "." else f"/docs/{rel_str}"
