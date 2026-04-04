# SSH-Docs

[![PyPI version](https://badge.fury.io/py/ssh-docs.svg)](https://badge.fury.io/py/ssh-docs)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Expose documentation via SSH** - designed for AI coding agents and developers who prefer the terminal.

SSH-Docs starts a read-only SSH server that lets AI agents and developers browse documentation using familiar Unix commands (`ls`, `cd`, `cat`, `find`, `grep`, `head`, `tail`, `pwd`).

**Why SSH for AI Agents?**
- Agents already use shell commands for code exploration
- No need to embed docs in prompts or rely on stale context
- Agents can search, filter, and read exactly what they need
- Works with any agent that can execute shell commands
- Inspired by [Supabase's approach](https://supabase.com) to agent-accessible documentation

## Features

- Read-only documentation browsing over SSH
- Familiar shell commands for navigating and searching files
- Zero-config startup with automatic content-root detection
- Optional YAML configuration via `.ssh-docs.yml`
- Public, password, or authorized-keys authentication modes
- Built-in shell completion generation for Bash, Zsh, and Fish
- Basic rate limiting controls in configuration
- Automatic site-name detection from `pyproject.toml`, `package.json`, or the current directory
- **Automatic agent integration files** - Generates AGENTS.md, SETUP.md, and SKILL.md at the root for AI coding agents

## Agent Integration (Primary Use Case)

SSH-Docs is designed primarily for AI coding agents. When you start a server, it automatically generates three integration files at the documentation root:

- **AGENTS.md** - Quick reference commands for agents to access your docs
- **SETUP.md** - Detailed setup instructions for different agent systems  
- **SKILL.md** - Skill definition for skill-based agent frameworks

### Quick Start for Agents

```bash
# 1. Start server (public auth recommended for agents)
ssh-docs serve ./docs --auth public --site-name "My Project"

# 2. Agents can immediately read integration instructions
ssh localhost -p 2222 'cat AGENTS.md'

# 3. Add to your project's agent configuration
ssh localhost -p 2222 'cat AGENTS.md' >> AGENTS.md

# 4. Or install as a skill
mkdir -p .agents/skills/my-project-docs
ssh localhost -p 2222 'cat SKILL.md' > .agents/skills/my-project-docs/SKILL.md
```

### Production Deployment for Agents

For production use with a public hostname:

```bash
# Deploy with custom hostname for agent instructions
ssh-docs serve ./docs \
  --hostname docs.example.com \
  --port 22 \
  --auth key \
  --keys-file ~/.ssh/authorized_keys
```

The `--hostname` option sets the public address that appears in agent instructions (AGENTS.md, SETUP.md, SKILL.md), while the server binds to the interface specified by `--host` (default: `127.0.0.1`).

**Example:** If you deploy on a server with domain `docs.example.com` but bind to all interfaces (`--host 0.0.0.0`), use `--hostname docs.example.com` so agents get the correct connection command:

```bash
ssh docs.example.com 'grep -rl "auth" /docs'
```

See [AGENT_INTEGRATION.md](AGENT_INTEGRATION.md) for detailed documentation and examples.

## Installation

```bash
pip install ssh-docs
```

## Quick Start

### No-Auth Mode (Recommended for Agents)

Public (no-auth) mode is the recommended setup for AI coding agents and local development:

```bash
# Serve with no authentication required
ssh-docs serve ./docs --auth public

# Or serve current directory with no auth
ssh-docs serve --auth public
```

Agents can then connect without credentials:

```bash
# Direct connection
ssh localhost -p 2222

# Or execute commands directly
ssh localhost -p 2222 'grep -rl "authentication" /docs'
ssh localhost -p 2222 'cat /docs/guides/getting-started.md'
```

**Why no-auth for agents?**
- Agents can access docs without credential management
- Simpler integration into agent workflows
- Ideal for local development and internal networks
- Can be combined with network-level security (firewall, VPN)

### Basic Usage

```bash
# Serve an auto-detected docs directory (uses public auth by default)
ssh-docs serve

# Serve a specific directory
ssh-docs serve ./docs

# Use a custom port
ssh-docs serve ./docs --port 3000
```

If you bind to a non-default host or port, connect with the same values:

```bash
ssh 127.0.0.1 -p 3000
```

### Available shell commands

Once connected, SSH-Docs exposes these commands:

```text
pwd, ls, cd, cat, head, tail, find, grep, help, exit
```

Example session:

```bash
/docs$ ls
/docs$ cd guides
/docs$ cat getting-started.md
/docs$ grep -R "authentication" .
/docs$ find . -name "*.md"
/docs$ head -n 20 README.md
/docs$ tail -n 10 changelog.txt
/docs$ pwd
/docs$ help
/docs$ exit
```

## CLI Commands

### `ssh-docs serve`

Start the SSH documentation server.

**Arguments:**
- `CONTENT_DIR` — directory to serve

**Options:**
- `-p, --port` — port to listen on (default: 2222)
- `-n, --site-name` — site name shown in shell/banner and agent instructions
- `-c, --config` — path to a config file
- `--host` — network interface to bind to (default: `127.0.0.1`)
  - Use `0.0.0.0` to bind to all interfaces
  - Use `127.0.0.1` for localhost only
- `--hostname` — public hostname for agent instructions (default: `localhost`)
  - This is the address agents will use to connect
  - Example: `docs.example.com`, `my-server.local`, `192.168.1.100`
  - Appears in generated AGENTS.md, SETUP.md, and SKILL.md files
- `--auth` — authentication mode: `public`, `key`, or `password` (default: `public`)
- `--keys-file` — authorized keys file for key authentication
- `--password` — password for password authentication
- `--no-config` — ignore `.ssh-docs.yml`
- `--log-level` — one of `debug`, `info`, `warn`, `error`

**Examples:**

```bash
# Local development (default)
ssh-docs serve ./docs

# Custom port and site name
ssh-docs serve ./docs --port 3000 --site-name "My API Docs"

# Public deployment with custom hostname for agents
ssh-docs serve ./docs \
  --host 0.0.0.0 \
  --hostname docs.example.com \
  --port 22 \
  --auth key

# Internal network with IP address
ssh-docs serve ./docs \
  --host 0.0.0.0 \
  --hostname 192.168.1.100 \
  --port 2222

# Password-protected
ssh-docs serve --auth password --password secret123

# Using config file
ssh-docs serve --config production.yml
```

### `ssh-docs init`

Create a `.ssh-docs.yml` configuration file.

**Options:**
- `--interactive` — prompt for common settings
- `--template` — accepts `basic` or `advanced`

Examples:

```bash
ssh-docs init
ssh-docs init --interactive
```

### `ssh-docs validate`

Validate a config file.

Examples:

```bash
ssh-docs validate
ssh-docs validate custom-config.yml
```

### `ssh-docs keygen`

Generate SSH host keys.

**Options:**
- `--output-dir` — output directory for generated keys
- `--force` — overwrite existing keys

Examples:

```bash
ssh-docs keygen
ssh-docs keygen --output-dir ./keys
```

### `ssh-docs completion`

Generate a shell completion script.

**Required option:**
- `--shell` — one of `bash`, `zsh`, or `fish`

Examples:

```bash
ssh-docs completion --shell bash
ssh-docs completion --shell zsh
ssh-docs completion --shell fish
```

## Configuration

SSH-Docs optionally loads `.ssh-docs.yml` from the current directory.

Example:

```yaml
site_name: "My Project Documentation"
content_root: "./docs"
port: 2222
host: "0.0.0.0"  # Bind to all network interfaces
hostname: "docs.example.com"  # Public hostname for agent instructions

auth:
  type: "public" # public, key, password
  # authorized_keys: "~/.ssh/authorized_keys"
  # password: "${SSH_DOCS_PASSWORD}"

server:
  banner: |
    Welcome to {site_name} Documentation
    Type 'help' for available commands
  max_connections: 10
  timeout: 300
  log_level: "info"
  # log_file: "./ssh-docs.log"

features:
  syntax_highlighting: false
  line_numbers: false
  search_index: false

ignore:
  - "*.pyc"
  - "__pycache__"
  - ".git"
  - "node_modules"

rate_limiting:
  enabled: true
  max_connections_per_ip: 3
  max_connections_per_minute: 10
  max_failed_auth_attempts: 5
  failed_auth_window_seconds: 300
  max_total_connections: 100
```

### Config behavior

- If no config file exists, SSH-Docs runs with defaults.
- Relative `content_root` values are resolved relative to the config file.
- Passwords can be read from environment variables like `${SSH_DOCS_PASSWORD}`.
- If `content_root` is not set explicitly, SSH-Docs auto-detects one of: `docs/`, `documentation/`, `public/`, `dist/`, otherwise it falls back to the current directory.

## Authentication

### Public access

Public mode disables authentication entirely:

```bash
ssh-docs serve ./docs --auth public
```

### Password authentication

```bash
ssh-docs serve ./docs --auth password --password secret123
```

Or with an environment variable in config:

```bash
export SSH_DOCS_PASSWORD="secret123"
ssh-docs serve
```

### Authorized keys authentication

```bash
ssh-docs serve ./docs --auth key --keys-file ~/.ssh/authorized_keys
```

## Shell Completion

Generate and install completions for your shell.

### Bash

```bash
ssh-docs completion --shell bash >> ~/.bashrc
source ~/.bashrc
```

### Zsh

```bash
ssh-docs completion --shell zsh >> ~/.zshrc
source ~/.zshrc
```

### Fish

```bash
ssh-docs completion --shell fish >> ~/.config/fish/config.fish
source ~/.config/fish/config.fish
```

## Auto-Detection

SSH-Docs automatically detects:

- **Content root** from `docs/`, `documentation/`, `public/`, or `dist/`
- **Site name** from `package.json`, `pyproject.toml`, or the current directory

## Requirements

- Python 3.8+
- `asyncssh`
- `click`
- `pyyaml`

## Development

```bash
git clone https://github.com/kourgeorge/ssh-docs.git
cd ssh-docs
pip install -e .
python -m ssh_docs serve ./docs
```

## Security Notes

- File browsing is read-only
- Content access is restricted to the configured content root
- Authentication can be disabled, password-based, or key-based
- Rate limiting settings are available in config
- Logging can be configured with a log level and optional log file

## License

MIT License.

## Support

- GitHub: https://github.com/kourgeorge/ssh-docs
- Issues: https://github.com/kourgeorge/ssh-docs/issues
- PyPI: https://pypi.org/project/ssh-docs/

---

**Made for developers who prefer the terminal.**
