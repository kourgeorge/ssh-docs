"""SSH server implementation for SSH-Docs."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

import asyncssh

from .config import Config
from .shell_factory import DefaultShellFactory
from .rate_limiter import RateLimiter, RateLimitConfig


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
        
        # Create shell factory with dependencies
        self.shell_factory = DefaultShellFactory(
            content_root=self.content_root,
            site_name=self.config.site_name,
            banner=self.config.banner,
        )
        
        # Initialize rate limiter if enabled
        self.rate_limiter: Optional[RateLimiter] = None
        if config.rate_limiting_enabled:
            rate_limit_config = RateLimitConfig(
                max_connections_per_ip=config.max_connections_per_ip,
                max_connections_per_minute=config.max_connections_per_minute,
                max_failed_auth_attempts=config.max_failed_auth_attempts,
                failed_auth_window_seconds=config.failed_auth_window_seconds,
                max_total_connections=config.max_total_connections,
            )
            self.rate_limiter = RateLimiter(rate_limit_config)
            logger.info("Rate limiting enabled")

    async def start(self) -> None:
        """Start the SSH server."""
        # Start rate limiter if enabled
        if self.rate_limiter:
            await self.rate_limiter.start()
        
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
        
        elif self.config.auth_type == "public":
            # Public access - no authentication required
            # Don't enable any auth methods; begin_auth() will return False to skip auth
            logger.warning("Server running in PUBLIC mode - no authentication required!")
        
        else:
            raise ValueError(f"Invalid auth_type: {self.config.auth_type}")
        
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
        
        # Stop rate limiter if enabled
        if self.rate_limiter:
            await self.rate_limiter.stop()



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
        self._peer_ip: Optional[str] = None
        self._connection_allowed = True

    def connection_made(self, conn: asyncssh.SSHServerConnection) -> None:
        """Called when a connection is established."""
        peer = conn.get_extra_info("peername")
        self._peer_ip = peer[0] if peer else "unknown"
        self._conn = conn
        logger.info(f"Connection from {self._peer_ip}")
        
        # Check rate limiting asynchronously
        if self.server.rate_limiter:
            import asyncio
            asyncio.create_task(self._check_rate_limit())
    
    async def _check_rate_limit(self) -> None:
        """Async helper to check rate limiting."""
        if not self.server.rate_limiter or not self._peer_ip:
            return
        
        allowed, reason = await self.server.rate_limiter.check_connection_allowed(self._peer_ip)
        
        if not allowed:
            logger.warning(f"Connection rejected from {self._peer_ip}: {reason}")
            self._connection_allowed = False
            if self._conn:
                self._conn.close()
            return
        
        # Record the connection
        await self.server.rate_limiter.record_connection(self._peer_ip)

    def connection_lost(self, exc: Optional[Exception]) -> None:
        """Called when connection is lost."""
        if exc:
            logger.error(f"Connection lost with error: {exc}")
        else:
            logger.info("Connection closed")
        
        # Record disconnection for rate limiting
        if self.server.rate_limiter and self._peer_ip and self._connection_allowed:
            import asyncio
            asyncio.create_task(
                self.server.rate_limiter.record_disconnection(self._peer_ip)
            )

    def begin_auth(self, username: str) -> bool:
        """Begin authentication for a user."""
        logger.debug(f"Authentication attempt for user: {username}")
        
        # Reject if connection was not allowed by rate limiter
        if not self._connection_allowed:
            return False
        
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
        """Validate password for a user.
        
        Note: This should never be called in public mode since password_auth
        is not enabled and begin_auth() returns False.
        """
        if self.server.config.auth_type != "password":
            logger.warning(f"validate_password called with auth_type={self.server.config.auth_type}")
            return False
        
        if not self.server.config.password:
            logger.error("Password auth enabled but no password configured")
            return False
        
        is_valid = password == self.server.config.password
        
        # Track authentication attempts for rate limiting
        if self.server.rate_limiter and self._peer_ip:
            import asyncio
            if is_valid:
                asyncio.create_task(
                    self.server.rate_limiter.record_auth_success(self._peer_ip)
                )
            else:
                asyncio.create_task(
                    self.server.rate_limiter.record_auth_failure(self._peer_ip)
                )
        
        return is_valid
    
    def session_requested(self):
        """Handle session request by returning a session handler."""
        return SSHDocsSession(self.server, self.server.shell_factory)


class SSHDocsSession(asyncssh.SSHServerSession):
    """SSH session handler for interactive shell."""
    
    def __init__(self, server: SSHDocsServer, shell_factory: DefaultShellFactory) -> None:
        self.server = server
        self.shell_factory = shell_factory
        self._shell = None
        self._chan = None
        self._term_type = None
        self._term_size = (80, 24, 0, 0)
        self._input_queue = asyncio.Queue()
    
    def connection_made(self, chan: asyncssh.SSHServerChannel) -> None:
        """Called when the session channel is opened."""
        self._chan = chan
        logger.info("Session channel opened")
    
    def pty_requested(self, term_type: str, term_size: tuple, term_modes: dict) -> bool:
        """Handle PTY (pseudo-terminal) request."""
        self._term_type = term_type
        self._term_size = term_size
        logger.info(f"PTY requested: type={term_type}, size={term_size}")
        # Accept PTY request - this is crucial for interactive features like tab completion
        return True
    
    def shell_requested(self) -> bool:
        """Handle shell request - return True to accept."""
        logger.info("Shell requested")
        return True
    
    def terminal_size_changed(self, width: int, height: int, pixwidth: int, pixheight: int) -> None:
        """Handle terminal size changes."""
        self._term_size = (width, height, pixwidth, pixheight)
        logger.debug(f"Terminal size changed: {width}x{height}")
    
    def data_received(self, data: str, datatype: int) -> None:
        """Called when data is received from the client."""
        if datatype is None:  # Regular stdin data
            # Put each character into the queue for the shell to process
            for char in data:
                self._input_queue.put_nowait(char)
    
    def eof_received(self) -> bool:
        """Called when EOF is received from the client."""
        logger.info("EOF received")
        self._input_queue.put_nowait(None)  # Signal EOF
        return True
    
    def session_started(self) -> None:
        """Called when the session is ready to start."""
        logger.info("Session started, creating shell")
        self._shell = self.shell_factory.create_shell(
            input_queue=self._input_queue,
            stdout=self._chan,
            stderr=self._chan,
        )
        # Start the shell in the background
        asyncio.create_task(self._run_shell())
    
    async def _run_shell(self) -> None:
        """Run the shell session."""
        try:
            logger.info("Running shell")
            await self._shell.run()
            logger.info("Shell ended normally")
        except Exception as e:
            logger.error(f"Shell error: {e}", exc_info=True)
        finally:
            if self._chan:
                self._chan.close()
                logger.info("Channel closed")





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
