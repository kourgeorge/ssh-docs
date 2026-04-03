"""Interactive shell session for SSH-Docs server."""

from __future__ import annotations

import os
import re
import shlex
from pathlib import Path
from typing import Any, Callable, Optional


class SSHDocsShell:
    """Interactive shell session that provides Unix-like commands for browsing documentation."""

    def __init__(
        self,
        stdin: Any,
        stdout: Any,
        stderr: Any,
        content_root: Path,
        site_name: str,
        banner: Optional[str] = None,
    ) -> None:
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.content_root = content_root.resolve()
        self.site_name = site_name
        self.cwd = "/site"
        self.banner = banner or self._default_banner()

    def _default_banner(self) -> str:
        return f"""Connected to {self.site_name}.ssh-docs
Source root: {self.content_root}
Mounted content: /site
Supported commands: pwd, ls, cd, cat, head, tail, find, grep, help, exit
Readonly session

"""

    async def run(self) -> None:
        """Main command loop."""
        self.stdout.write(self.banner)

        while True:
            try:
                self.stdout.write(f"{self.cwd}$ ")
                line = await self.stdin.readline()
                if not line:
                    break

                raw = line.strip()
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

    async def _execute_command(self, cmd: str, args: list[str]) -> None:
        """Execute a single command."""
        commands: dict[str, Callable] = {
            "help": self.cmd_help,
            "pwd": self.cmd_pwd,
            "ls": self.cmd_ls,
            "cd": self.cmd_cd,
            "cat": self.cmd_cat,
            "head": self.cmd_head,
            "tail": self.cmd_tail,
            "find": self.cmd_find,
            "grep": self.cmd_grep,
        }

        if cmd in commands:
            await commands[cmd](args)
        else:
            self.stdout.write(f"unsupported command: {cmd}\n")

    def _resolve_virtual_path(self, value: Optional[str]) -> str:
        """Resolve a path argument to a normalized virtual path."""
        if not value:
            return self.cwd
        candidate = value if value.startswith("/") else str(Path(self.cwd) / value)
        normalized = os.path.normpath(candidate).replace("\\", "/")
        if not normalized.startswith("/site"):
            return "/invalid"
        return normalized

    def _to_real_path(self, virtual_path: str) -> Optional[Path]:
        """Convert virtual path to real filesystem path with security checks."""
        if not virtual_path.startswith("/site"):
            return None
        rel = virtual_path.removeprefix("/site").lstrip("/")
        target = (self.content_root / rel).resolve()
        try:
            target.relative_to(self.content_root)
        except ValueError:
            return None
        return target

    def _to_virtual_path(self, path: Path) -> str:
        """Convert real filesystem path to virtual path."""
        rel = path.relative_to(self.content_root)
        rel_str = str(rel).replace("\\", "/")
        return "/site" if rel_str == "." else f"/site/{rel_str}"

    async def cmd_help(self, args: list[str]) -> None:
        """Display available commands."""
        self.stdout.write("Commands: pwd, ls, cd, cat, head, tail, find, grep, help, exit\n")

    async def cmd_pwd(self, args: list[str]) -> None:
        """Print current working directory."""
        self.stdout.write(f"{self.cwd}\n")

    async def cmd_ls(self, args: list[str]) -> None:
        """List directory contents."""
        virtual_path = self._resolve_virtual_path(args[0] if args else None)
        real_path = self._to_real_path(virtual_path)

        if virtual_path == "/invalid" or real_path is None or not real_path.exists():
            self.stdout.write(f"ls: no such file or directory: {virtual_path}\n")
            return

        if real_path.is_file():
            self.stdout.write(f"{real_path.name}\n")
            return

        for child in sorted(real_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
            self.stdout.write(f"{child.name}\n")

    async def cmd_cd(self, args: list[str]) -> None:
        """Change current directory."""
        virtual_path = self._resolve_virtual_path(args[0] if args else "/site")
        real_path = self._to_real_path(virtual_path)

        if virtual_path == "/invalid" or real_path is None or not real_path.exists():
            self.stdout.write(f"cd: no such file or directory: {virtual_path}\n")
            return

        if not real_path.is_dir():
            self.stdout.write(f"cd: not a directory: {virtual_path}\n")
            return

        self.cwd = virtual_path

    async def cmd_cat(self, args: list[str]) -> None:
        """Display file contents."""
        file_path = await self._require_file_arg("cat", args)
        if file_path is None:
            return

        try:
            content = file_path.read_text(encoding="utf-8")
            self.stdout.write(content.rstrip() + "\n")
        except UnicodeDecodeError:
            self.stdout.write("cat: cannot read binary file\n")

    async def cmd_head(self, args: list[str]) -> None:
        """Display first lines of a file."""
        await self._print_slice("head", args, tail=False)

    async def cmd_tail(self, args: list[str]) -> None:
        """Display last lines of a file."""
        await self._print_slice("tail", args, tail=True)

    async def _print_slice(self, command: str, args: list[str], tail: bool) -> None:
        """Helper for head/tail commands."""
        if not args:
            self.stdout.write(f"{command}: missing file operand\n")
            return

        count = 10
        file_index = 0

        if len(args) >= 2 and args[0] == "-n":
            try:
                count = int(args[1])
            except ValueError:
                self.stdout.write(f"{command}: invalid line count\n")
                return
            file_index = 2

        if file_index >= len(args):
            self.stdout.write(f"{command}: missing file operand\n")
            return

        file_path = await self._require_file_arg(command, [args[file_index]])
        if file_path is None:
            return

        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
            selected = lines[-count:] if tail else lines[:count]
            self.stdout.write("\n".join(selected) + "\n")
        except UnicodeDecodeError:
            self.stdout.write(f"{command}: cannot read binary file\n")

    async def _require_file_arg(self, command: str, args: list[str]) -> Optional[Path]:
        """Validate and return file path from arguments."""
        if not args:
            self.stdout.write(f"{command}: missing file operand\n")
            return None

        virtual_path = self._resolve_virtual_path(args[0])
        real_path = self._to_real_path(virtual_path)

        if virtual_path == "/invalid" or real_path is None or not real_path.exists():
            self.stdout.write(f"{command}: no such file: {virtual_path}\n")
            return None

        if not real_path.is_file():
            self.stdout.write(f"{command}: is a directory: {virtual_path}\n")
            return None

        return real_path

    async def cmd_find(self, args: list[str]) -> None:
        """Find files matching criteria."""
        start_virtual = self._resolve_virtual_path(args[0] if args else self.cwd)
        start_real = self._to_real_path(start_virtual)

        if start_virtual == "/invalid" or start_real is None or not start_real.exists():
            self.stdout.write(f"find: no such file or directory: {start_virtual}\n")
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
            self.stdout.write(f"{self._to_virtual_path(path)}\n")

    def _matches_name(self, name: str, pattern: str) -> bool:
        """Check if filename matches glob pattern."""
        regex = "^" + re.escape(pattern).replace(r"\*", ".*") + "$"
        return re.match(regex, name) is not None

    async def cmd_grep(self, args: list[str]) -> None:
        """Search file contents."""
        recursive = False
        filtered: list[str] = []

        for arg in args:
            if arg == "-R":
                recursive = True
            else:
                filtered.append(arg)

        if len(filtered) < 2:
            self.stdout.write("grep: usage: grep [-R] <pattern> <path>\n")
            return

        pattern = filtered[0]
        start_virtual = self._resolve_virtual_path(filtered[1])
        start_real = self._to_real_path(start_virtual)

        if start_virtual == "/invalid" or start_real is None or not start_real.exists():
            self.stdout.write(f"grep: no such file or directory: {start_virtual}\n")
            return

        if start_real.is_dir() and not recursive:
            self.stdout.write("grep: path is a directory, use -R\n")
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
                    self.stdout.write(f"{self._to_virtual_path(target)}:{index}:{line}\n")

        if not found:
            self.stdout.write("grep: no matches\n")
