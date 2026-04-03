"""Command-line interface for SSH-Docs."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click

from .config import (
    Config,
    auto_detect_content_root,
    auto_detect_site_name,
    generate_default_config,
    load_config,
)
from .server import run_server


@click.group()
@click.version_option(version="0.1.0", prog_name="ssh-docs")
def cli() -> None:
    """SSH-Docs: Expose documentation via SSH.
    
    Browse your documentation using familiar Unix commands over SSH.
    """
    pass


@cli.command()
@click.argument("content_dir", type=click.Path(exists=True), required=False)
@click.option(
    "-p",
    "--port",
    type=int,
    default=None,
    help="Port to listen on [default: 2222]",
)
@click.option(
    "-n",
    "--site-name",
    type=str,
    default=None,
    help="Site name for banner [default: auto-detect]",
)
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True),
    default=None,
    help="Config file path [default: .ssh-docs.yml]",
)
@click.option(
    "--host",
    type=str,
    default=None,
    help="Host to bind to [default: 0.0.0.0]",
)
@click.option(
    "--auth",
    type=click.Choice(["public", "key", "password"]),
    default=None,
    help="Auth type [default: public]",
)
@click.option(
    "--keys-file",
    type=click.Path(exists=True),
    default=None,
    help="Authorized keys file (for key auth)",
)
@click.option(
    "--password",
    type=str,
    default=None,
    help="Password (for password auth)",
)
@click.option(
    "--no-config",
    is_flag=True,
    help="Ignore config file",
)
@click.option(
    "--log-level",
    type=click.Choice(["debug", "info", "warn", "error"]),
    default=None,
    help="Log level [default: info]",
)
def serve(
    content_dir: Optional[str],
    port: Optional[int],
    site_name: Optional[str],
    config: Optional[str],
    host: Optional[str],
    auth: Optional[str],
    keys_file: Optional[str],
    password: Optional[str],
    no_config: bool,
    log_level: Optional[str],
) -> None:
    """Start SSH documentation server.
    
    Examples:
    
      \b
      # Serve current directory on default port
      ssh-docs serve
      
      \b
      # Serve specific directory
      ssh-docs serve ./docs
      
      \b
      # Custom port and site name
      ssh-docs serve ./docs -p 3000 -n "My API Docs"
      
      \b
      # Use config file
      ssh-docs serve --config custom-config.yml
      
      \b
      # Password authentication
      ssh-docs serve --auth password --password secret123
    """
    # Load config from file if not disabled
    if not no_config:
        try:
            cfg = load_config(config)
        except Exception as e:
            if config:  # Only error if explicitly specified
                click.echo(f"Error loading config: {e}", err=True)
                sys.exit(1)
            cfg = Config()
    else:
        cfg = Config()
    
    # Override with CLI arguments
    if content_dir:
        cfg.content_root = Path(content_dir)
    elif cfg.content_root == Path("."):
        # Auto-detect if not specified
        cfg.content_root = auto_detect_content_root()
    
    if port is not None:
        cfg.port = port
    
    if site_name:
        cfg.site_name = site_name
    elif cfg.site_name == "Documentation":
        # Auto-detect if default
        cfg.site_name = auto_detect_site_name()
    
    if host:
        cfg.host = host
    
    if auth:
        cfg.auth_type = auth
    
    if keys_file:
        cfg.authorized_keys = keys_file
    
    if password:
        cfg.password = password
    
    if log_level:
        cfg.log_level = log_level
    
    # Validate configuration
    if not cfg.content_root.exists():
        click.echo(f"Error: Content directory does not exist: {cfg.content_root}", err=True)
        sys.exit(1)
    
    if not cfg.content_root.is_dir():
        click.echo(f"Error: Content path is not a directory: {cfg.content_root}", err=True)
        sys.exit(1)
    
    if cfg.auth_type == "password" and not cfg.password:
        click.echo("Error: Password authentication requires --password option", err=True)
        sys.exit(1)
    
    if cfg.auth_type == "key" and not cfg.authorized_keys:
        click.echo("Error: Key authentication requires --keys-file option", err=True)
        sys.exit(1)
    
    # Run server
    try:
        asyncio.run(run_server(cfg))
    except KeyboardInterrupt:
        click.echo("\nServer stopped")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--interactive",
    is_flag=True,
    help="Interactive setup wizard",
)
@click.option(
    "--template",
    type=click.Choice(["basic", "advanced"]),
    default="basic",
    help="Config template to use",
)
def init(interactive: bool, template: str) -> None:
    """Initialize .ssh-docs.yml config file.
    
    Creates a configuration file with sensible defaults.
    
    Examples:
    
      \b
      # Create basic config
      ssh-docs init
      
      \b
      # Interactive setup
      ssh-docs init --interactive
    """
    config_path = Path(".ssh-docs.yml")
    
    if config_path.exists():
        if not click.confirm(f"{config_path} already exists. Overwrite?"):
            click.echo("Aborted")
            return
    
    if interactive:
        click.echo("SSH-Docs Configuration Setup\n")
        
        site_name = click.prompt("Site name", default="My Documentation")
        
        # Auto-detect content directory
        detected = auto_detect_content_root()
        content_dir = click.prompt(
            "Content directory",
            default=str(detected),
        )
        
        port = click.prompt("Port", default=2222, type=int)
        
        auth_type = click.prompt(
            "Authentication type",
            type=click.Choice(["public", "key", "password"]),
            default="public",
        )
        
        config_content = generate_default_config(site_name, content_dir, port)
        
        # Modify auth section if needed
        if auth_type != "public":
            lines = config_content.split("\n")
            for i, line in enumerate(lines):
                if 'type: "public"' in line:
                    lines[i] = f'  type: "{auth_type}"'
                    break
            config_content = "\n".join(lines)
    else:
        # Use defaults with auto-detection
        detected_root = auto_detect_content_root()
        detected_name = auto_detect_site_name()
        config_content = generate_default_config(
            detected_name,
            str(detected_root),
            2222,
        )
    
    # Write config file
    config_path.write_text(config_content, encoding="utf-8")
    
    click.echo(f"✓ Created {config_path}")
    click.echo(f"\nTo start the server, run:")
    click.echo(f"  ssh-docs serve")


@cli.command()
@click.argument(
    "config_file",
    type=click.Path(exists=True),
    default=".ssh-docs.yml",
    required=False,
)
def validate(config_file: str) -> None:
    """Validate configuration file.
    
    Checks syntax and settings in the config file.
    
    Examples:
    
      \b
      # Validate default config
      ssh-docs validate
      
      \b
      # Validate specific config
      ssh-docs validate custom-config.yml
    """
    try:
        cfg = load_config(config_file)
        
        click.echo(f"✓ Configuration is valid")
        click.echo(f"\nSettings:")
        click.echo(f"  Site name: {cfg.site_name}")
        click.echo(f"  Content root: {cfg.content_root}")
        click.echo(f"  Port: {cfg.port}")
        click.echo(f"  Host: {cfg.host}")
        click.echo(f"  Auth type: {cfg.auth_type}")
        
        # Check content root
        if not cfg.content_root.exists():
            click.echo(f"\n⚠ Warning: Content root does not exist: {cfg.content_root}", err=True)
        elif not cfg.content_root.is_dir():
            click.echo(f"\n⚠ Warning: Content root is not a directory: {cfg.content_root}", err=True)
        
    except FileNotFoundError:
        click.echo(f"Error: Config file not found: {config_file}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--output-dir",
    type=click.Path(),
    default=None,
    help="Where to save keys [default: ~/.ssh-docs/keys]",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing keys",
)
def keygen(output_dir: Optional[str], force: bool) -> None:
    """Generate SSH host keys for the server.
    
    Creates RSA key pair for SSH server authentication.
    
    Examples:
    
      \b
      # Generate keys in default location
      ssh-docs keygen
      
      \b
      # Generate keys in custom location
      ssh-docs keygen --output-dir ./keys
    """
    try:
        import asyncssh
    except ImportError:
        click.echo("Error: asyncssh is required. Install with: pip install asyncssh", err=True)
        sys.exit(1)
    
    if output_dir:
        key_dir = Path(output_dir)
    else:
        key_dir = Path.home() / ".ssh-docs" / "keys"
    
    key_dir.mkdir(parents=True, exist_ok=True)
    key_path = key_dir / "ssh_host_rsa_key"
    
    if key_path.exists() and not force:
        click.echo(f"Error: Key already exists: {key_path}", err=True)
        click.echo("Use --force to overwrite", err=True)
        sys.exit(1)
    
    click.echo(f"Generating RSA key pair...")
    
    key = asyncssh.generate_private_key("ssh-rsa")
    key.write_private_key(str(key_path))
    
    # Also write public key
    pub_key_path = key_path.with_suffix(".pub")
    key.write_public_key(str(pub_key_path))
    
    click.echo(f"✓ Private key: {key_path}")
    click.echo(f"✓ Public key: {pub_key_path}")
    click.echo(f"\nTo use this key, add to your config:")
    click.echo(f"  host_key: {key_path}")


def main() -> None:
    """Main entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
