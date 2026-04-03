"""Configuration management for SSH-Docs server."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class Config:
    """Configuration container for SSH-Docs server."""

    def __init__(self, data: Optional[dict[str, Any]] = None) -> None:
        data = data or {}
        
        # Basic settings
        self.site_name: str = data.get("site_name", "Documentation")
        self.content_root: Path = Path(data.get("content_root", ".")).expanduser()
        self.port: int = data.get("port", 2222)
        self.host: str = data.get("host", "0.0.0.0")
        
        # Authentication
        auth_data = data.get("auth", {})
        self.auth_type: str = auth_data.get("type", "public")
        self.authorized_keys: Optional[str] = auth_data.get("authorized_keys")
        self.password: Optional[str] = auth_data.get("password")
        
        # Server settings
        server_data = data.get("server", {})
        self.banner: Optional[str] = server_data.get("banner")
        self.max_connections: int = server_data.get("max_connections", 10)
        self.timeout: int = server_data.get("timeout", 300)
        self.log_level: str = server_data.get("log_level", "info")
        self.log_file: Optional[str] = server_data.get("log_file")
        
        # Features
        features_data = data.get("features", {})
        self.syntax_highlighting: bool = features_data.get("syntax_highlighting", False)
        self.line_numbers: bool = features_data.get("line_numbers", False)
        self.search_index: bool = features_data.get("search_index", False)
        
        # Custom commands
        self.custom_commands: list[dict[str, Any]] = data.get("custom_commands", [])
        
        # Path mappings
        self.mounts: list[dict[str, str]] = data.get("mounts", [])
        
        # Ignore patterns
        self.ignore: list[str] = data.get("ignore", [])
        
        # Host key path
        self.host_key: Optional[Path] = None
        if "host_key" in data:
            self.host_key = Path(data["host_key"]).expanduser()
        
        # Rate limiting
        rate_limit_data = data.get("rate_limiting", {})
        self.rate_limiting_enabled: bool = rate_limit_data.get("enabled", True)
        self.max_connections_per_ip: int = rate_limit_data.get("max_connections_per_ip", 3)
        self.max_connections_per_minute: int = rate_limit_data.get("max_connections_per_minute", 10)
        self.max_failed_auth_attempts: int = rate_limit_data.get("max_failed_auth_attempts", 5)
        self.failed_auth_window_seconds: float = rate_limit_data.get("failed_auth_window_seconds", 300.0)
        self.max_total_connections: int = rate_limit_data.get("max_total_connections", 100)

    def __repr__(self) -> str:
        return f"Config(site_name={self.site_name!r}, port={self.port}, content_root={self.content_root})"


def load_config(config_path: Optional[str] = None) -> Config:
    """Load configuration from YAML file.
    
    Args:
        config_path: Path to config file. If None, looks for .ssh-docs.yml in current directory.
        
    Returns:
        Config object with loaded settings.
        
    Raises:
        FileNotFoundError: If config file doesn't exist.
        ValueError: If YAML parsing fails or yaml module not installed.
    """
    if config_path is None:
        config_path = ".ssh-docs.yml"
    
    path = Path(config_path)
    
    if not path.exists():
        # Return default config if file doesn't exist
        return Config()
    
    if not HAS_YAML:
        raise ValueError(
            "PyYAML is required to load config files. Install with: pip install pyyaml"
        )
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            
        if data is None:
            data = {}
            
        # Resolve paths relative to config file location
        if "content_root" in data:
            content_root = Path(data["content_root"])
            if not content_root.is_absolute():
                data["content_root"] = str(path.parent / content_root)
        
        # Expand environment variables in password
        if "auth" in data and "password" in data["auth"]:
            password = data["auth"]["password"]
            if password.startswith("${") and password.endswith("}"):
                env_var = password[2:-1]
                data["auth"]["password"] = os.environ.get(env_var)
        
        return Config(data)
        
    except yaml.YAMLError as e:
        raise ValueError(f"Failed to parse config file: {e}")


def generate_default_config(
    site_name: str = "My Documentation",
    content_root: str = "./docs",
    port: int = 2222,
) -> str:
    """Generate a default configuration file content.
    
    Args:
        site_name: Name of the documentation site.
        content_root: Path to documentation content.
        port: Port to listen on.
        
    Returns:
        YAML configuration file content as string.
    """
    return f"""# SSH-Docs Configuration File

# Basic settings
site_name: "{site_name}"
content_root: "{content_root}"
port: {port}
host: "0.0.0.0"

# Authentication
auth:
  type: "public"  # Options: public, key, password
  # For key-based auth:
  # authorized_keys: "~/.ssh/authorized_keys"
  # For password auth:
  # password: "${{SSH_DOCS_PASSWORD}}"  # Use environment variable

# Server settings
server:
  banner: |
    Welcome to {{site_name}} Documentation
    Type 'help' for available commands
  max_connections: 10
  timeout: 300  # seconds
  log_level: "info"  # Options: debug, info, warn, error
  # log_file: "./ssh-docs.log"

# Features
features:
  syntax_highlighting: false
  line_numbers: false
  search_index: false

# Custom commands (optional)
# custom_commands:
#   - name: "changelog"
#     description: "Show changelog"
#     type: "file"
#     path: "/CHANGELOG.md"

# Path mappings (optional)
# mounts:
#   - virtual: "/api"
#     real: "./api-docs"

# Ignore patterns (like .gitignore)
ignore:
  - "*.pyc"
  - "__pycache__"
  - ".git"
  - "node_modules"

# Rate limiting (security)
rate_limiting:
  enabled: true
  max_connections_per_ip: 3
  max_connections_per_minute: 10
  max_failed_auth_attempts: 5
  failed_auth_window_seconds: 300  # 5 minutes
  max_total_connections: 100
"""


def auto_detect_content_root() -> Path:
    """Auto-detect documentation directory.
    
    Looks for common documentation directories in order:
    - docs/
    - documentation/
    - public/
    - dist/
    - Current directory as fallback
    
    Returns:
        Path to detected content directory.
    """
    candidates = ["docs", "documentation", "public", "dist"]
    
    for candidate in candidates:
        path = Path(candidate)
        if path.exists() and path.is_dir():
            return path
    
    return Path(".")


def auto_detect_site_name() -> str:
    """Auto-detect site name from project files.
    
    Checks in order:
    - package.json (name field)
    - pyproject.toml (project.name field)
    - Directory name
    
    Returns:
        Detected site name.
    """
    # Try package.json
    package_json = Path("package.json")
    if package_json.exists():
        try:
            import json
            with open(package_json, "r") as f:
                data = json.load(f)
                if "name" in data:
                    return data["name"]
        except Exception:
            pass
    
    # Try pyproject.toml
    pyproject = Path("pyproject.toml")
    if pyproject.exists():
        try:
            try:
                import tomllib
            except ImportError:
                tomllib = None
            
            if tomllib:
                with open(pyproject, "rb") as f:
                    data = tomllib.load(f)
                    if "project" in data and "name" in data["project"]:
                        return data["project"]["name"]
        except Exception:
            pass
    
    # Fallback to directory name
    return Path.cwd().name
