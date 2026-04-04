# SSH-Docs

[![PyPI version](https://badge.fury.io/py/ssh-docs.svg)](https://badge.fury.io/py/ssh-docs)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Expose documentation via SSH** for developers and AI coding agents using familiar Unix-style commands.

SSH-Docs starts a read-only SSH server for a directory of files and gives connected users a small shell with commands like `ls`, `cd`, `cat`, `find`, `grep`, `head`, `tail`, `pwd`, and `help`.

This generalizes the docs-over-SSH approach: instead of asking an agent to rely on stale context, you let it browse current markdown docs through the same shell workflow it already uses for code exploration.

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

## Agent Integration

SSH-Docs automatically generates three files at the documentation root to help AI coding agents discover and use your docs:

- **AGENTS.md** - Quick reference commands for accessing your documentation
- **SETUP.md** - Detailed setup instructions for different agent systems
- **SKILL.md** - Skill definition for skill-based agent frameworks

These files are available immediately when you start the server:

```bash
# Start server
ssh-docs serve ./docs --auth public --site-name "My Project"

# Agents can read integration instructions
ssh localhost -p 2222
/docs$ cat AGENTS.md
/docs$ cat SETUP.md
/docs$ cat SKILL.md
```

Agents can then add your docs to their project configuration:

```bash
# Append to project's AGENTS.md
ssh localhost -p 2222 'cat AGENTS.md' >> AGENTS.md

# Or install as a skill
mkdir -p .agents/skills/my-project-docs
ssh localhost -p 2222 'cat SKILL.md' > .agents/skills/my-project-docs/SKILL.md
```

This pattern is inspired by [Supabase's approach](https://supabase.com) to exposing documentation to AI agents. See [AGENT_INTEGRATION.md](AGENT_INTEGRATION.md) for detailed documentation.

## Installation

```bash
pip install ssh-docs
```

## Quick Start

### No-Auth Mode (Recommended for Agents)

The simplest way to start is with public (no-auth) mode, which is ideal for AI coding agents and local development:

```bash
# Serve with no authentication required
ssh-docs serve ./docs --auth public

# Or serve current directory with no auth
ssh-docs serve --auth public
```

Then connect without any credentials:

```bash
ssh localhost -p 2222
```

This mode is perfect for:
- AI coding agents that need to browse documentation
- Local development and testing
- Internal networks where authentication isn't required
- Quick documentation sharing

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
- `-p, --port` — port to listen on
- `-n, --site-name` — site name shown in the shell/banner context
- `-c, --config` — path to a config file
- `--host` — host to bind to (e.g., `0.0.0.0`, `127.0.0.1`)
- `--hostname` — public hostname for agent instructions (e.g., `docs.example.com`, `localhost`)
- `--auth` — authentication mode: `public`, `key`, or `password`
- `--keys-file` — authorized keys file for key authentication
- `--password` — password for password authentication
- `--no-config` — ignore `.ssh-docs.yml`
- `--log-level` — one of `debug`, `info`, `warn`, `error`

**Examples:**

```bash
ssh-docs serve ./docs
ssh-docs serve ./docs --port 3000 --site-name "My API Docs"
ssh-docs serve --auth password --password secret123
ssh-docs serve --config production.yml

# Public deployment with custom hostname
ssh-docs serve ./docs --hostname docs.example.com --port 22
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
host: "0.0.0.0"
hostname: "localhost"  # Public hostname for agent instructions

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
