"""Command registry and dispatcher for SSH-Docs shell."""

from __future__ import annotations

from typing import Dict, Optional

from .base import BaseCommand, ShellContext


class CommandRegistry:
    """Registry for managing and dispatching shell commands.
    
    Provides a centralized way to register, lookup, and execute commands,
    decoupling the shell from individual command implementations.
    """
    
    def __init__(self) -> None:
        """Initialize empty command registry."""
        self._commands: Dict[str, type[BaseCommand]] = {}
    
    def register(self, command_class: type[BaseCommand]) -> None:
        """Register a command class.
        
        Args:
            command_class: The command class to register
            
        Raises:
            ValueError: If a command with the same name is already registered
        """
        # Access the class attribute directly - no need to instantiate
        name = command_class.name
        
        if not name:
            raise ValueError(f"Command class {command_class.__name__} must define 'name' class attribute")
        
        if name in self._commands:
            raise ValueError(f"Command '{name}' is already registered")
        
        self._commands[name] = command_class
    
    def get_command(self, name: str, context: ShellContext) -> Optional[BaseCommand]:
        """Get a command instance by name.
        
        Args:
            name: The command name
            context: Shell context to pass to the command
            
        Returns:
            Command instance if found, None otherwise
        """
        command_class = self._commands.get(name)
        if command_class is None:
            return None
        
        return command_class(context)
    
    def list_commands(self) -> list[str]:
        """Get list of all registered command names.
        
        Returns:
            Sorted list of command names
        """
        return sorted(self._commands.keys())
    
    def has_command(self, name: str) -> bool:
        """Check if a command is registered.
        
        Args:
            name: The command name to check
            
        Returns:
            True if command exists, False otherwise
        """
        return name in self._commands
    
    async def execute(self, name: str, args: list[str], context: ShellContext) -> bool:
        """Execute a command by name.
        
        Args:
            name: The command name
            args: Command arguments
            context: Shell context
            
        Returns:
            True if command was found and executed, False if not found
        """
        command = self.get_command(name, context)
        if command is None:
            return False
        
        await command.execute(args)
        return True
