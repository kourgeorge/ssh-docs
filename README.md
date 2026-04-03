# SSH-Docs

[![PyPI version](https://badge.fury.io/py/ssh-docs.svg)](https://badge.fury.io/py/ssh-docs)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Expose documentation via SSH** - Browse your documentation using familiar Unix commands over SSH.

**🎉 Now available on PyPI!** Install with: `pip install ssh-docs`

## Features

- 🔒 **Secure SSH Access** - Standard SSH protocol with authentication options
- 📁 **Read-Only Browsing** - Safe exploration of documentation files
- 🛠️ **Unix Commands** - Familiar commands: `ls`, `cd`, `cat`, `grep`, `find`, `head`, `tail`
- ⚙️ **Zero Config** - Works out of the box with sensible defaults
- 🎨 **Customizable** - Optional YAML configuration for advanced setups
- 🚀 **Easy Setup** - Single command to start serving docs

## Installation

```bash
pip install ssh-docs
```

## Quick Start

### Serve Documentation (Zero Config)

```bash
# Serve current directory
ssh-docs serve

# Serve specific directory
ssh-docs serve ./docs

# Custom port
ssh-docs serve ./docs -p 3000
```

Then connect:

```bash
ssh localhost -p 2222
```

### Basic Commands

Once connected, use familiar Unix commands:

```bash
/site$ ls                    # List files
/site$ cd docs              # Change directory
/site$ cat README.md        # View file
/site$ grep "API" -R .      # Search content
/site$ find . -name "*.md"  # Find files
/site$ head -n 20 file.txt  # First 20 lines
/site$ tail -n 10 file.txt  # Last 10 lines
/site$ pwd                  # Current directory
/site$ help                 # Show commands
/site$ exit                 # Close session
```

## Configuration

### Initialize Config File

```bash
# Create .ssh-docs.yml with defaults
ssh-docs init

# Interactive setup
ssh-docs init --interactive
```

### Configuration File (.ssh-docs.yml)

```yaml
# Basic settings
site_name: "My Project Documentation"
content_root: "./docs"
port: 2222
host: "0.0.0.0"

# Authentication
auth:
  type: "public"  # Options: public, key, password
  # For key-based auth:
  # authorized_keys: "~/.ssh/authorized_keys"
  # For password auth:
  # password: "${SSH_DOCS_PASSWORD}"

# Server settings
server:
  banner: |
    Welcome to {site_name} Documentation
    Type 'help' for available commands
  max_connections: 10
  timeout: 300
  log_level: "info"

# Ignore patterns
ignore:
  - "*.pyc"
  - "__pycache__"
  - ".git"
  - "node_modules"
```

## Authentication

### Public Access (Default)

No authentication required - anyone can connect:

```bash
ssh-docs serve ./docs
```

### Password Authentication

```bash
ssh-docs serve ./docs --auth password --password secret123
```

Or use environment variable:

```bash
export SSH_DOCS_PASSWORD="secret123"
ssh-docs serve ./docs --auth password
```

### Key-Based Authentication

```bash
ssh-docs serve ./docs --auth key --keys-file ~/.ssh/authorized_keys
```

## Advanced Usage

### Generate Host Keys

```bash
# Generate keys in default location
ssh-docs keygen

# Custom location
ssh-docs keygen --output-dir ./keys
```

### Validate Configuration

```bash
# Validate default config
ssh-docs validate

# Validate specific config
ssh-docs validate custom-config.yml
```

### Using Config File

```bash
# Use default .ssh-docs.yml
ssh-docs serve

# Use custom config
ssh-docs serve --config production.yml

# Ignore config file
ssh-docs serve --no-config
```

## CLI Reference

### `ssh-docs serve`

Start SSH documentation server.

**Options:**
- `CONTENT_DIR` - Directory to serve (default: auto-detect)
- `-p, --port` - Port to listen on (default: 2222)
- `-n, --site-name` - Site name for banner (default: auto-detect)
- `-c, --config` - Config file path (default: .ssh-docs.yml)
- `--host` - Host to bind to (default: 0.0.0.0)
- `--auth` - Auth type: public, key, password (default: public)
- `--keys-file` - Authorized keys file (for key auth)
- `--password` - Password (for password auth)
- `--no-config` - Ignore config file
- `--log-level` - Log level: debug, info, warn, error

**Examples:**

```bash
# Basic usage
ssh-docs serve ./docs

# Custom port and name
ssh-docs serve ./docs -p 3000 -n "My API Docs"

# Password auth
ssh-docs serve --auth password --password secret123

# Use config file
ssh-docs serve --config production.yml
```

### `ssh-docs init`

Initialize configuration file.

**Options:**
- `--interactive` - Interactive setup wizard
- `--template` - Template: basic, advanced

**Examples:**

```bash
# Create basic config
ssh-docs init

# Interactive setup
ssh-docs init --interactive
```

### `ssh-docs validate`

Validate configuration file.

**Examples:**

```bash
# Validate default config
ssh-docs validate

# Validate specific config
ssh-docs validate custom-config.yml
```

### `ssh-docs keygen`

Generate SSH host keys.

**Options:**
- `--output-dir` - Where to save keys (default: ~/.ssh-docs/keys)
- `--force` - Overwrite existing keys

**Examples:**

```bash
# Generate in default location
ssh-docs keygen

# Custom location
ssh-docs keygen --output-dir ./keys
```

## Use Cases

### Local Development

```bash
# Serve docs while developing
cd my-project
ssh-docs serve ./docs
```

### CI/CD Integration

```bash
# In Dockerfile or CI script
pip install ssh-docs
ssh-docs serve /app/docs --port 2222 &
```

### Production Deployment

```yaml
# docker-compose.yml
services:
  docs:
    image: python:3.11
    command: sh -c "pip install ssh-docs && ssh-docs serve /docs"
    ports:
      - "2222:2222"
    volumes:
      - ./docs:/docs:ro
```

### Documentation Server

```bash
# Production setup with auth
ssh-docs init --interactive
ssh-docs keygen
ssh-docs serve --auth key --keys-file ~/.ssh/authorized_keys
```

## Security Considerations

- **Read-Only**: All operations are read-only by default
- **Path Traversal Protection**: Prevents access outside content root
- **Authentication**: Supports password and key-based auth
- **Connection Limits**: Configurable max connections
- **Timeouts**: Automatic session timeouts

## Auto-Detection

SSH-Docs automatically detects:

- **Content Directory**: Looks for `docs/`, `documentation/`, `public/`, `dist/`
- **Site Name**: Reads from `package.json`, `pyproject.toml`, or directory name
- **Host Keys**: Generates if not present

## Requirements

- Python 3.8+
- asyncssh
- click
- pyyaml (optional, for config files)

## Development

```bash
# Clone repository
git clone https://github.com/ssh-docs/ssh-docs.git
cd ssh-docs

# Install in development mode
pip install -e .

# Run tests
pytest

# Run locally
python -m ssh_docs serve ./demo-website
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

## Support

- GitHub Issues: https://github.com/ssh-docs/ssh-docs/issues
- Documentation: https://github.com/ssh-docs/ssh-docs#readme

## Roadmap

- [ ] Syntax highlighting for code files
- [ ] Search index for faster grep
- [ ] Custom command plugins
- [ ] Docker image
- [ ] NPM package wrapper
- [ ] Web-based terminal viewer
- [ ] Session recording/replay
- [ ] Multi-user support with permissions

---

**Made with ❤️ for developers who love the terminal**
