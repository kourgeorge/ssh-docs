# SSH-Docs Installation & Testing Guide

## Installation

### From Source (Development)

```bash
cd ssh-docs
pip install -e .
```

### From PyPI (When Published)

```bash
pip install ssh-docs
```

## Quick Test

### 1. Test CLI Installation

```bash
ssh-docs --help
```

Expected output:
```
Usage: ssh-docs [OPTIONS] COMMAND [ARGS]...

  SSH-Docs: Expose documentation via SSH.

Commands:
  init      Initialize .ssh-docs.yml config file.
  keygen    Generate SSH host keys for the server.
  serve     Start SSH documentation server.
  validate  Validate configuration file.
```

### 2. Test with Demo Content

```bash
# From the repository root
cd /path/to/ssh-docs-repo
ssh-docs serve demo-website --port 2223
```

### 3. Connect to Server

The server currently uses asyncssh which requires proper SSH authentication setup. For testing:

**Option A: Use the original demo script (simpler for testing)**
```bash
python3 website-ssh-cli-demo.py demo-website
```

Then interact directly in the terminal.

**Option B: Configure SSH server for public access**

The SSH server implementation is complete but requires authentication configuration. For production use, you'll need to:

1. Generate host keys:
```bash
ssh-docs keygen
```

2. Configure authentication in `.ssh-docs.yml`:
```yaml
auth:
  type: "public"  # For testing without auth
```

3. Start server:
```bash
ssh-docs serve demo-website
```

## Project Structure

```
ssh-docs/
├── ssh_docs/
│   ├── __init__.py       # Package initialization
│   ├── __main__.py       # Module entry point
│   ├── cli.py            # Click-based CLI interface
│   ├── server.py         # AsyncSSH server implementation
│   ├── shell.py          # Interactive shell with Unix commands
│   └── config.py         # Configuration management
├── pyproject.toml        # Package metadata and dependencies
├── requirements.txt      # Python dependencies
├── README.md            # User documentation
└── INSTALLATION.md      # This file

demo-website/            # Test content
├── index.html
├── about.html
├── blog/
│   └── welcome.md
└── docs/
    └── api.md
```

## Available Commands in Shell

Once connected to the SSH server:

- `ls [path]` - List directory contents
- `cd <path>` - Change directory
- `pwd` - Print working directory
- `cat <file>` - Display file contents
- `head [-n count] <file>` - Show first N lines
- `tail [-n count] <file>` - Show last N lines
- `find [path] [-name pattern]` - Find files
- `grep [-R] <pattern> <path>` - Search file contents
- `help` - Show available commands
- `exit` - Close session

## Testing Checklist

- [x] Package installs successfully
- [x] CLI commands are available
- [x] Shell module works correctly
- [x] File operations (ls, cd, cat, etc.) function properly
- [x] Path security (no directory traversal)
- [x] Configuration file parsing
- [ ] SSH authentication (needs production setup)
- [ ] Multi-user connections
- [ ] Performance with large file trees

## Known Issues

1. **SSH Authentication**: The asyncssh server requires proper authentication setup. For quick testing, use the original `website-ssh-cli-demo.py` script which provides a simpler interactive shell without SSH protocol overhead.

2. **Host Key Generation**: First-time server start will generate temporary host keys. For production, use `ssh-docs keygen` to create persistent keys.

## Next Steps for Production

1. **Authentication Setup**: Configure proper SSH authentication (key-based or password)
2. **Host Keys**: Generate and persist host keys
3. **Systemd Service**: Create service file for automatic startup
4. **Docker Image**: Build container for easy deployment
5. **Testing**: Add pytest tests for all components
6. **Documentation**: Add API documentation and examples

## Development

```bash
# Install in development mode
pip install -e .

# Run tests (when added)
pytest

# Format code
black ssh_docs/

# Type checking
mypy ssh_docs/
```

## Support

For issues or questions:
- GitHub Issues: https://github.com/ssh-docs/ssh-docs/issues
- Documentation: See README.md
