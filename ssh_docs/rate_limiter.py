"""Rate limiting and connection tracking for SSH-Docs server.

Provides protection against:
- Brute force authentication attacks
- Denial of Service (DoS) attacks
- Connection flooding
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class ConnectionStats:
    """Statistics for a single IP address."""
    
    # Connection tracking
    total_connections: int = 0
    active_connections: int = 0
    last_connection_time: float = 0.0
    
    # Authentication tracking
    failed_auth_attempts: int = 0
    successful_auth_attempts: int = 0
    last_failed_auth_time: float = 0.0
    
    # Rate limiting state
    blocked_until: float = 0.0
    block_count: int = 0


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting behavior."""
    
    # Connection limits
    max_connections_per_ip: int = 3
    max_connections_per_minute: int = 10
    
    # Authentication limits
    max_failed_auth_attempts: int = 5
    failed_auth_window_seconds: float = 300.0  # 5 minutes
    
    # Blocking behavior
    initial_block_duration: float = 60.0  # 1 minute
    max_block_duration: float = 3600.0  # 1 hour
    block_duration_multiplier: float = 2.0
    
    # Cleanup
    cleanup_interval_seconds: float = 300.0  # 5 minutes
    stats_retention_seconds: float = 3600.0  # 1 hour
    
    # Global limits
    max_total_connections: int = 100


class RateLimiter:
    """Rate limiter with IP-based tracking and exponential backoff.
    
    Features:
    - Per-IP connection limits
    - Failed authentication tracking
    - Exponential backoff for repeated violations
    - Automatic cleanup of old statistics
    - Thread-safe operation
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None) -> None:
        """Initialize rate limiter.
        
        Args:
            config: Rate limiting configuration (uses defaults if None)
        """
        self.config = config or RateLimitConfig()
        self._stats: Dict[str, ConnectionStats] = defaultdict(ConnectionStats)
        self._lock = asyncio.Lock()
        self._total_connections = 0
        self._cleanup_task: Optional[asyncio.Task] = None
        
        logger.info(
            f"Rate limiter initialized: "
            f"max_connections_per_ip={self.config.max_connections_per_ip}, "
            f"max_failed_auth={self.config.max_failed_auth_attempts}"
        )
    
    async def start(self) -> None:
        """Start the rate limiter background tasks."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Rate limiter cleanup task started")
    
    async def stop(self) -> None:
        """Stop the rate limiter background tasks."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
            logger.info("Rate limiter cleanup task stopped")
    
    async def check_connection_allowed(self, ip_address: str) -> tuple[bool, Optional[str]]:
        """Check if a new connection from an IP is allowed.
        
        Args:
            ip_address: IP address of the connecting client
            
        Returns:
            Tuple of (allowed, reason). If not allowed, reason contains explanation.
        """
        async with self._lock:
            current_time = time.time()
            stats = self._stats[ip_address]
            
            # Check if IP is currently blocked
            if stats.blocked_until > current_time:
                remaining = int(stats.blocked_until - current_time)
                logger.warning(
                    f"Connection blocked from {ip_address}: "
                    f"blocked for {remaining} more seconds"
                )
                return False, f"Too many violations. Blocked for {remaining} more seconds."
            
            # Check global connection limit
            if self._total_connections >= self.config.max_total_connections:
                logger.warning(
                    f"Connection rejected from {ip_address}: "
                    f"global limit reached ({self._total_connections})"
                )
                return False, "Server at maximum capacity. Please try again later."
            
            # Check per-IP active connection limit
            if stats.active_connections >= self.config.max_connections_per_ip:
                logger.warning(
                    f"Connection rejected from {ip_address}: "
                    f"per-IP limit reached ({stats.active_connections})"
                )
                return False, f"Too many active connections from your IP address."
            
            # Check connection rate (connections per minute)
            time_since_last = current_time - stats.last_connection_time
            if time_since_last < 60.0:  # Within last minute
                if stats.total_connections >= self.config.max_connections_per_minute:
                    logger.warning(
                        f"Connection rejected from {ip_address}: "
                        f"rate limit exceeded ({stats.total_connections} in last minute)"
                    )
                    return False, "Too many connection attempts. Please slow down."
            else:
                # Reset counter if more than a minute has passed
                stats.total_connections = 0
            
            return True, None
    
    async def record_connection(self, ip_address: str) -> None:
        """Record a new connection from an IP address.
        
        Args:
            ip_address: IP address of the connecting client
        """
        async with self._lock:
            stats = self._stats[ip_address]
            stats.total_connections += 1
            stats.active_connections += 1
            stats.last_connection_time = time.time()
            self._total_connections += 1
            
            logger.debug(
                f"Connection recorded from {ip_address}: "
                f"active={stats.active_connections}, total={stats.total_connections}"
            )
    
    async def record_disconnection(self, ip_address: str) -> None:
        """Record a disconnection from an IP address.
        
        Args:
            ip_address: IP address of the disconnecting client
        """
        async with self._lock:
            stats = self._stats[ip_address]
            if stats.active_connections > 0:
                stats.active_connections -= 1
                self._total_connections -= 1
                
                logger.debug(
                    f"Disconnection recorded from {ip_address}: "
                    f"active={stats.active_connections}"
                )
    
    async def record_auth_failure(self, ip_address: str) -> None:
        """Record a failed authentication attempt.
        
        Args:
            ip_address: IP address of the client
        """
        async with self._lock:
            current_time = time.time()
            stats = self._stats[ip_address]
            
            # Reset counter if outside the window
            time_since_last_failure = current_time - stats.last_failed_auth_time
            if time_since_last_failure > self.config.failed_auth_window_seconds:
                stats.failed_auth_attempts = 0
            
            stats.failed_auth_attempts += 1
            stats.last_failed_auth_time = current_time
            
            logger.warning(
                f"Failed auth from {ip_address}: "
                f"attempt {stats.failed_auth_attempts}/{self.config.max_failed_auth_attempts}"
            )
            
            # Check if we should block this IP
            if stats.failed_auth_attempts >= self.config.max_failed_auth_attempts:
                await self._block_ip(ip_address, stats)
    
    async def record_auth_success(self, ip_address: str) -> None:
        """Record a successful authentication.
        
        Args:
            ip_address: IP address of the client
        """
        async with self._lock:
            stats = self._stats[ip_address]
            stats.successful_auth_attempts += 1
            # Reset failed attempts on successful auth
            stats.failed_auth_attempts = 0
            
            logger.info(f"Successful auth from {ip_address}")
    
    async def _block_ip(self, ip_address: str, stats: ConnectionStats) -> None:
        """Block an IP address with exponential backoff.
        
        Args:
            ip_address: IP address to block
            stats: Connection statistics for the IP
        """
        # Calculate block duration with exponential backoff
        block_duration = min(
            self.config.initial_block_duration * (
                self.config.block_duration_multiplier ** stats.block_count
            ),
            self.config.max_block_duration
        )
        
        stats.blocked_until = time.time() + block_duration
        stats.block_count += 1
        stats.failed_auth_attempts = 0  # Reset counter
        
        logger.warning(
            f"IP {ip_address} blocked for {block_duration:.0f} seconds "
            f"(block #{stats.block_count})"
        )
    
    async def _cleanup_loop(self) -> None:
        """Background task to clean up old statistics."""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval_seconds)
                await self._cleanup_old_stats()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)
    
    async def _cleanup_old_stats(self) -> None:
        """Remove statistics for IPs that haven't connected recently."""
        async with self._lock:
            current_time = time.time()
            cutoff_time = current_time - self.config.stats_retention_seconds
            
            ips_to_remove = [
                ip for ip, stats in self._stats.items()
                if (stats.active_connections == 0 and
                    stats.last_connection_time < cutoff_time and
                    stats.blocked_until < current_time)
            ]
            
            for ip in ips_to_remove:
                del self._stats[ip]
            
            if ips_to_remove:
                logger.debug(f"Cleaned up stats for {len(ips_to_remove)} IPs")
    
    async def get_stats(self, ip_address: Optional[str] = None) -> Dict:
        """Get statistics for monitoring.
        
        Args:
            ip_address: Optional IP to get specific stats for
            
        Returns:
            Dictionary with statistics
        """
        async with self._lock:
            if ip_address:
                stats = self._stats.get(ip_address)
                if stats:
                    return {
                        "ip": ip_address,
                        "active_connections": stats.active_connections,
                        "total_connections": stats.total_connections,
                        "failed_auth_attempts": stats.failed_auth_attempts,
                        "successful_auth_attempts": stats.successful_auth_attempts,
                        "is_blocked": stats.blocked_until > time.time(),
                        "blocked_until": stats.blocked_until if stats.blocked_until > time.time() else None,
                    }
                return None
            
            # Global stats
            return {
                "total_active_connections": self._total_connections,
                "tracked_ips": len(self._stats),
                "blocked_ips": sum(
                    1 for stats in self._stats.values()
                    if stats.blocked_until > time.time()
                ),
            }
