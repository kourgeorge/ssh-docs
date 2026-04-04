# Agent Integration Guide

SSH-Docs automatically generates three files at the root of your documentation to help AI coding agents discover and use your docs:

- **AGENTS.md** - Quick reference for agents to access your docs
- **SETUP.md** - Instructions for setting up agent integration
- **SKILL.md** - Skill definition for skill-based agent systems

## How It Works

When you start an SSH-Docs server, these files are automatically created as virtual files at the root of your documentation. Agents connecting via SSH can read these files to learn how to access your documentation.

## Example Usage

### 1. Start Your Server

```bash
ssh-docs serve ./docs --auth public --port 2222 --site-name "My Project"
```

### 2. Agents Can Discover Integration Instructions

```bash
# Connect and read the agent instructions
ssh localhost -p 2222
/docs$ cat AGENTS.md
```

### 3. Add to Your Project's AGENTS.md

Agents can append the instructions to your project's agent configuration:

```bash
# For projects using AGENTS.md
ssh localhost -p 2222 'cat AGENTS.md' >> AGENTS.md

# For projects using other files
ssh localhost -p 2222 'cat AGENTS.md' >> CLAUDE.md
ssh localhost -p 2222 'cat AGENTS.md' >> GEMINI.md
```

## Generated Files

### AGENTS.md

Contains quick reference commands for accessing your documentation:

```markdown
## My Project

Before working on a My Project feature, check the docs via `ssh localhost -p 2222 <command>`.

```bash
# Search for a topic
ssh localhost -p 2222 grep -rl 'auth' /docs

# Read a specific guide
ssh localhost -p 2222 cat /docs/guides/getting-started.md

# Find all guides in a section
ssh localhost -p 2222 find /docs -name '*.md'

# Search with context
ssh localhost -p 2222 grep -r 'keyword' /docs --include='*.md' -l
```

All docs live under `/docs` as markdown files.
```

### SETUP.md

Provides detailed setup instructions for different agent systems:

- Instructions for appending to agent config files
- Skill installation paths for different tools
- Support for Claude Code, Cursor, GitHub Copilot, Bob Shell, and more

### SKILL.md

A skill definition file that can be installed in skill-based agent systems:

```markdown
---
name: my-project-docs
description: Search and read My Project documentation using a bash shell.
---

# My Project Docs

Search and read My Project documentation over SSH.
```

## Customization

The generated files automatically include:

- Your site name (from `--site-name` or config)
- Your SSH host and port
- The correct documentation path (`/docs`)

## Integration Patterns

### Pattern 1: Append to Project AGENTS.md

Best for projects that already have an AGENTS.md file:

```bash
ssh your-docs.example.com 'cat AGENTS.md' >> AGENTS.md
```

### Pattern 2: Install as Skill

Best for agent systems that support skills:

```bash
mkdir -p .agents/skills/my-project-docs
ssh your-docs.example.com 'cat SKILL.md' > .agents/skills/my-project-docs/SKILL.md
```

### Pattern 3: Both

For maximum compatibility:

```bash
# Add to instructions
ssh your-docs.example.com 'cat AGENTS.md' >> AGENTS.md

# Install skill
mkdir -p .agents/skills/my-project-docs
ssh your-docs.example.com 'cat SKILL.md' > .agents/skills/my-project-docs/SKILL.md
```

## Supported Agent Tools

The generated files include instructions for:

- **Claude Code** (`.claude/` directory)
- **GitHub Copilot** (`.github/` directory)
- **Cursor** (`.cursor/` directory)
- **OpenCode** (`.opencode/` directory)
- **Gemini CLI** (`.gemini/` directory)
- **Bob Shell** (`.bob/` directory)
- **Generic** (`.agents/` directory)

## Example: Supabase Pattern

This feature is inspired by Supabase's approach to exposing documentation to agents:

```bash
# Supabase exposes docs at /supabase/docs/
ssh supabase.sh grep -rl 'auth' /supabase/docs/

# Your project can do the same
ssh your-docs.example.com grep -rl 'auth' /docs
```

## Production Deployment for Agents

For production deployment where AI agents will access your documentation:

### 1. Deploy with Public Hostname

```bash
ssh-docs serve ./docs \
  --host 0.0.0.0 \
  --hostname docs.yourproject.com \
  --port 22 \
  --auth key \
  --keys-file ~/.ssh/authorized_keys
```

### 2. Understanding `--host` vs `--hostname`

These two options serve different purposes:

| Option | Purpose | Example | Used For |
|--------|---------|---------|----------|
| `--host` | Network interface to bind to | `0.0.0.0`, `127.0.0.1` | Server binding |
| `--hostname` | Public address for agents | `docs.example.com`, `192.168.1.100` | Agent instructions |

**Why separate them?**
- `--host` controls which network interface the server listens on
  - `127.0.0.1` = localhost only (default)
  - `0.0.0.0` = all network interfaces
- `--hostname` sets the address that appears in agent instructions (AGENTS.md, SETUP.md, SKILL.md)
  - This is what agents will use to connect
  - Can be a domain name, IP address, or hostname

**Example scenarios:**

```bash
# Local development (agents connect to localhost)
ssh-docs serve ./docs
# Binds to: 127.0.0.1:2222
# Agent instructions use: localhost:2222

# Internal network (agents connect via IP)
ssh-docs serve ./docs --host 0.0.0.0 --hostname 192.168.1.100
# Binds to: 0.0.0.0:2222 (all interfaces)
# Agent instructions use: 192.168.1.100:2222

# Public deployment (agents connect via domain)
ssh-docs serve ./docs --host 0.0.0.0 --hostname docs.example.com --port 22
# Binds to: 0.0.0.0:22 (all interfaces)
# Agent instructions use: docs.example.com
```

### 3. Production Configuration File

Create `.ssh-docs.yml`:

```yaml
site_name: "My Project Documentation"
content_root: "./docs"
port: 22
host: "0.0.0.0"  # Bind to all network interfaces
hostname: "docs.yourproject.com"  # Public hostname for agent instructions

auth:
  type: "key"
  authorized_keys: "~/.ssh/authorized_keys"

server:
  banner: |
    Welcome to My Project Documentation
    Type 'help' for available commands
  max_connections: 50
  timeout: 600

rate_limiting:
  enabled: true
  max_connections_per_ip: 10
  max_connections_per_minute: 30
```

Then start with:

```bash
ssh-docs serve --config .ssh-docs.yml
```

### 4. Agent Instructions Will Use Your Hostname

With `--hostname docs.yourproject.com`, the generated AGENTS.md will contain:

```bash
# Search for a topic
ssh docs.yourproject.com grep -rl 'auth' /docs

# Read a specific guide
ssh docs.yourproject.com cat /docs/guides/getting-started.md
```

Instead of:

```bash
ssh localhost -p 2222 grep -rl 'auth' /docs
```

This ensures agents have the correct connection information regardless of where they run.

## Benefits

1. **Self-Documenting**: Agents can discover how to use your docs
2. **Standardized**: Follows common patterns used by major projects
3. **Flexible**: Works with multiple agent systems
4. **Automatic**: No manual file creation needed
5. **Always Up-to-Date**: Generated dynamically based on your server config

## See Also

- [SSH-Docs README](README.md)
- [Configuration Guide](.ssh-docs.yml)
- [Supabase Docs Pattern](https://supabase.com)
