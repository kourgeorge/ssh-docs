"""SSH server implementation for SSH-Docs."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

import asyncssh

from .config import Config
from .shell import SSHDocsShell


logger = logging.getLogger(__name__)


class SSHDocsServer:
    """SSH server that provides documentation browsing capabilities."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.content_root = config.content_root.resolve()
        self.server: Optional[asyncssh.SSHAcceptor] = None
        
        # Ensure content root exists
        if not self.content_root.exists():
            raise ValueError(f"Content root does not exist: {self.content_root}")
        if not self.content_root.is_dir():
            raise ValueError(f"Content root is not a directory: {self.content_root}")

    async def start(self) -> None:
        """Start the SSH server."""
        # Generate or load host key
        host_key = await self._get_host_key()
        
        # Configure server options
        server_options = {
            "server_host_keys": [host_key],
            "encoding": "utf-8",  # Use UTF-8 encoding for text
        }
        
        # Add authentication if configured
        if self.config.auth_type == "password" and self.config.password:
            server_options["password_auth"] = True
            
        elif self.config.auth_type == "key" and self.config.authorized_keys:
            server_options["authorized_client_keys"] = self.config.authorized_keys
        
        else:
            # Public access - accept any connection without authentication
            # We enable password auth but accept any password
            server_options["password_auth"] = True
        
        logger.info(f"Starting SSH server on {self.config.host}:{self.config.port}")
        logger.info(f"Content root: {self.content_root}")
        logger.info(f"Site name: {self.config.site_name}")
        logger.info(f"Auth type: {self.config.auth_type}")
        
        try:
            self.server = await asyncssh.create_server(
                lambda: SSHDocsServerProtocol(self),
                host=self.config.host,
                port=self.config.port,
                **server_options,
            )
            
            logger.info("SSH server started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start SSH server: {e}")
            raise

    async def stop(self) -> None:
        """Stop the SSH server."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("SSH server stopped")



    async def _get_host_key(self) -> str:
        """Get or generate SSH host key."""
        if self.config.host_key and self.config.host_key.exists():
            logger.info(f"Using host key from: {self.config.host_key}")
            return str(self.config.host_key)
        
        # Generate temporary key
        logger.info("Generating temporary host key")
        key = asyncssh.generate_private_key("ssh-rsa")
        
        # Save to default location if possible
        key_dir = Path.home() / ".ssh-docs" / "keys"
        key_dir.mkdir(parents=True, exist_ok=True)
        key_path = key_dir / "ssh_host_rsa_key"
        
        try:
            key.write_private_key(str(key_path))
            logger.info(f"Saved host key to: {key_path}")
        except Exception as e:
            logger.warning(f"Could not save host key: {e}")
        
        return key


class SSHDocsServerProtocol(asyncssh.SSHServer):
    """SSH server protocol handler."""

    def __init__(self, server: SSHDocsServer) -> None:
        self.server = server

    def connection_made(self, conn: asyncssh.SSHServerConnection) -> None:
        """Called when a connection is established."""
        peer = conn.get_extra_info("peername")
        logger.info(f"Connection from {peer}")

    def connection_lost(self, exc: Optional[Exception]) -> None:
        """Called when connection is lost."""
        if exc:
            logger.error(f"Connection lost with error: {exc}")
        else:
            logger.info("Connection closed")

    def begin_auth(self, username: str) -> bool:
        """Begin authentication for a user."""
        logger.debug(f"Authentication attempt for user: {username}")
        
        # For public access, skip authentication entirely
        if self.server.config.auth_type == "public":
            # Returning False skips authentication
            return False
        
        return True

    def password_auth_supported(self) -> bool:
        """Check if password authentication is supported."""
        # Only support password auth for password mode, not public
        return self.server.config.auth_type == "password"
    
    def public_key_auth_supported(self) -> bool:
        """Check if public key authentication is supported."""
        # Support public key auth for key mode
        return self.server.config.auth_type == "key"
    
    def kbdint_auth_supported(self) -> bool:
        """Check if keyboard-interactive authentication is supported."""
        # Not supported
        return False

    def validate_password(self, username: str, password: str) -> bool:
        """Validate password for a user."""
        # For public access, accept any password
        if self.server.config.auth_type == "public":
            return True
            
        if self.server.config.auth_type != "password":
            return False
        
        if not self.server.config.password:
            return False
        
        return password == self.server.config.password
    
    def session_requested(self):
        """Handle session request by returning a handler function."""
        async def handle_session(stdin, stdout, stderr):
            """Handler function that receives stream objects."""
            shell = SSHDocsShell(
                stdin=stdin,
                stdout=stdout,
                stderr=stderr,
                content_root=self.server.content_root,
                site_name=self.server.config.site_name,
                banner=self.server.config.banner,
            )
            try:
                logger.info("Starting shell session")
                await shell.run()
                logger.info("Shell session ended normally")
            except Exception as e:
                logger.error(f"Shell error: {e}", exc_info=True)
            finally:
                # Close streams to signal session completion
                stdout.close()
                stderr.close()
                logger.info("Streams closed")
        
        return handle_session





async def run_server(config: Config) -> None:
    """Run the SSH server (convenience function).
    
    Args:
        config: Server configuration.
    """
    # Setup logging
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        filename=config.log_file if config.log_file else None,
    )
    
    server = SSHDocsServer(config)
    
    try:
        await server.start()
        
        # Keep server running
        print(f"SSH-Docs server running on {config.host}:{config.port}")
        print(f"Content: {config.content_root}")
        print(f"Connect with: ssh {config.host} -p {config.port}")
        print("Press Ctrl+C to stop")
        
        # Wait indefinitely
        await asyncio.Event().wait()
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await server.stop()
