"""Interactive shell session for SSH-Docs server."""

from __future__ import annotations

import shlex
from pathlib import Path
from typing import Any, Optional

from .commands import (
    CatCommand,
    CdCommand,
    CommandRegistry,
    FindCommand,
    GrepCommand,
    HeadCommand,
    HelpCommand,
    LsCommand,
    PathResolver,
    PwdCommand,
    ShellContext,
    TailCommand,
)
from .filesystem import FileSystemService, LocalFileSystem


class SSHDocsShell:
    """Interactive shell session that provides Unix-like commands for browsing documentation.
    
    This shell provides a lightweight, modular command architecture where each command
    is implemented as a separate class. The shell handles I/O, tab completion, and
    command dispatching, while individual commands handle their own logic.
    """

    def __init__(
        self,
        input_queue: Any,
        stdout: Any,
        stderr: Any,
        content_root: Path,
        site_name: str,
        banner: Optional[str] = None,
        filesystem: Optional[FileSystemService] = None,
    ) -> None:
        """Initialize the SSH-Docs shell.
        
        Args:
            input_queue: Async queue for reading user input
            stdout: Standard output stream
            stderr: Standard error stream
            content_root: Root directory of the documentation content
            site_name: Name of the documentation site
            banner: Optional custom banner message
            filesystem: File system service (defaults to LocalFileSystem)
        """
        self.input_queue = input_queue
        self.stdout = stdout
        self.stderr = stderr
        self.content_root = content_root.resolve()
        self.site_name = site_name
        self.banner = banner or self._default_banner()
        self.filesystem = filesystem or LocalFileSystem()
        
        # Initialize shell context with filesystem
        self.context = ShellContext(
            stdout=stdout,
            stderr=stderr,
            content_root=content_root,
            site_name=site_name,
            filesystem=self.filesystem,
        )
        
        # Initialize command registry and register all commands
        self.registry = CommandRegistry()
        self._register_commands()
        
        # Path resolver for tab completion
        self.path_resolver = PathResolver(content_root)

    def _register_commands(self) -> None:
        """Register all available commands."""
        self.registry.register(HelpCommand)
        self.registry.register(PwdCommand)
        self.registry.register(LsCommand)
        self.registry.register(CdCommand)
        self.registry.register(CatCommand)
        self.registry.register(HeadCommand)
        self.registry.register(TailCommand)
        self.registry.register(FindCommand)
        self.registry.register(GrepCommand)

    def _default_banner(self) -> str:
        """Generate default welcome banner."""
        return f""" ____  ____  _   _      ____   ___   ____ ____  
/ ___|/ ___|| | | |    |  _ \\ / _ \\ / ___/ ___| 
\\___ \\\\___ \\| |_| |____| | | | | | | |   \\___ \\ 
 ___) |___) |  _  |____| |_| | |_| | |___ ___) |
|____/|____/|_| |_|    |____/ \\___/ \\____|____/ 

Docs-over-SSH lets your agent browse SSH-Docs documentation directly using bash.

Connected to {self.site_name}.ssh-docs
Source root: {self.content_root}
Mounted content: /site
Supported commands: pwd, ls, cd, cat, head, tail, find, grep, help, exit
Readonly session

"""

    async def run(self) -> None:
        """Main command loop with tab completion support."""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info("Shell run() started")
        self.stdout.write(self.banner)
        logger.info("Banner written")

        current_line = ""
        
        while True:
            try:
                prompt = f"{self.context.cwd}$ "
                self.stdout.write(prompt)
                
                # Read input character by character to handle tab completion
                current_line = ""
                while True:
                    char = await self.input_queue.get()
                    
                    if char is None:
                        logger.info("Connection closed")
                        return
                    
                    # Handle tab completion
                    if char == '\t':
                        current_line = await self._handle_tab_completion(
                            current_line, prompt
                        )
                        continue
                    
                    # Handle backspace
                    elif char in ('\x7f', '\x08'):
                        if current_line:
                            current_line = current_line[:-1]
                            self.stdout.write('\b \b')
                        continue
                    
                    # Handle newline
                    elif char in ('\n', '\r'):
                        self.stdout.write('\n')
                        break
                    
                    # Handle Ctrl+C
                    elif char == '\x03':
                        self.stdout.write('^C\n')
                        current_line = ""
                        break
                    
                    # Handle Ctrl+D
                    elif char == '\x04':
                        if not current_line:
                            self.stdout.write('\nSession closed\n')
                            return
                        continue
                    
                    # Regular character
                    else:
                        current_line += char
                
                raw = current_line.strip()
                if not raw:
                    continue

                try:
                    parts = shlex.split(raw)
                except ValueError as exc:
                    self.stdout.write(f"parse error: {exc}\n")
                    continue

                cmd = parts[0]
                args = parts[1:]

                if cmd in {"exit", "quit"}:
                    self.stdout.write("Session closed\n")
                    break

                await self._execute_command(cmd, args)

            except (EOFError, KeyboardInterrupt):
                self.stdout.write("\nSession closed\n")
                break

    async def _handle_tab_completion(self, current_line: str, prompt: str) -> str:
        """Handle tab completion for commands and paths.
        
        Args:
            current_line: Current input line
            prompt: Shell prompt string
            
        Returns:
            Updated current line after completion
        """
        stripped = current_line.lstrip()
        leading_spaces = current_line[:len(current_line) - len(stripped)]
        parts = stripped.split()
        
        # Determine what to complete
        if not parts:
            # Empty line - show all commands
            completions = self.registry.list_commands()
        elif len(parts) == 1 and not stripped.endswith(' '):
            # Completing command name
            prefix = parts[0]
            completions = [
                cmd for cmd in self.registry.list_commands()
                if cmd.startswith(prefix)
            ]
        else:
            # Completing path argument
            if stripped.endswith(' '):
                prefix = ""
            else:
                prefix = parts[-1] if len(parts) > 1 else ""
            
            completions = self._complete_path(prefix)
        
        if len(completions) == 1:
            # Single match - complete it
            completion = completions[0]
            
            if not parts:
                current_line = leading_spaces + completion
            elif len(parts) == 1 and not stripped.endswith(' '):
                current_line = leading_spaces + completion
            else:
                if stripped.endswith(' '):
                    current_line = leading_spaces + stripped + completion
                else:
                    if len(parts) > 1:
                        current_line = leading_spaces + ' '.join(parts[:-1]) + ' ' + completion
                    else:
                        current_line = leading_spaces + completion
            
            # Clear line and rewrite
            self.stdout.write('\r' + ' ' * (len(prompt) + 100) + '\r')
            self.stdout.write(prompt + current_line)
            
        elif len(completions) > 1:
            # Multiple matches - show them
            self.stdout.write('\n')
            if len(completions) <= 10:
                for comp in completions:
                    self.stdout.write(f"{comp}  ")
            else:
                # Show in multiple columns for many items
                max_width = max(len(c) for c in completions) + 2
                cols = max(1, 80 // max_width)
                for i, comp in enumerate(completions):
                    self.stdout.write(comp.ljust(max_width))
                    if (i + 1) % cols == 0:
                        self.stdout.write('\n')
            self.stdout.write('\n')
            self.stdout.write(prompt + current_line)
        
        return current_line

    def _complete_path(self, prefix: str) -> list[str]:
        """Complete file and directory paths.
        
        Args:
            prefix: Path prefix to complete
            
        Returns:
            List of matching path completions
        """
        # Determine the directory to search and the prefix to match
        if prefix.startswith('/'):
            if prefix.endswith('/'):
                dir_part = prefix.rstrip('/')
                file_part = ''
            elif '/' in prefix.rstrip('/')[1:]:
                dir_part = prefix.rsplit('/', 1)[0] or '/'
                file_part = prefix.rsplit('/', 1)[1]
            else:
                dir_part = '/site'
                file_part = prefix[1:] if len(prefix) > 1 else ''
            virtual_path = dir_part
        else:
            if '/' in prefix:
                dir_part = prefix.rsplit('/', 1)[0]
                file_part = prefix.rsplit('/', 1)[1]
                virtual_path = self.path_resolver.resolve_virtual_path(
                    dir_part, self.context.cwd
                )
            else:
                dir_part = ''
                file_part = prefix
                virtual_path = self.context.cwd
        
        real_path = self.path_resolver.to_real_path(virtual_path)
        if not real_path or not real_path.exists() or not real_path.is_dir():
            return []
        
        # Get matching entries
        try:
            entries = []
            for child in sorted(
                real_path.iterdir(),
                key=lambda p: (not p.is_dir(), p.name.lower())
            ):
                name = child.name
                
                if not name.startswith(file_part):
                    continue
                
                # Build the completion string
                if prefix.startswith('/'):
                    full_name = self.path_resolver.to_virtual_path(child)
                elif dir_part:
                    full_name = f"{dir_part}/{name}"
                else:
                    full_name = name
                
                # Add trailing slash for directories
                if child.is_dir():
                    full_name += "/"
                
                entries.append(full_name)
            
            return entries
        except (PermissionError, OSError):
            return []

    async def _execute_command(self, cmd: str, args: list[str]) -> None:
        """Execute a single command.
        
        Args:
            cmd: Command name
            args: Command arguments
        """
        executed = await self.registry.execute(cmd, args, self.context)
        
        if not executed:
            self.stdout.write(f"unsupported command: {cmd}\n")
