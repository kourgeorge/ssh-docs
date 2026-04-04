"""Templates for agent integration files."""

from typing import Dict


def get_agents_md_template(site_name: str, ssh_host: str, docs_path: str) -> str:
    """Generate AGENTS.md content for agent instructions."""
    return f"""## {site_name}

Before working on a {site_name} feature, check the docs via `ssh {ssh_host} <command>`.

```bash
# Search for a topic
ssh {ssh_host} grep -rl 'auth' {docs_path}

# Read a specific guide
ssh {ssh_host} cat {docs_path}/guides/getting-started.md

# Find all guides in a section
ssh {ssh_host} find {docs_path} -name '*.md'

# Search with context
ssh {ssh_host} grep -r 'keyword' {docs_path} --include='*.md' -l
```

All docs live under `{docs_path}` as markdown files. You can use any standard Unix tools (grep, find, cat, etc.) to search and read them.
"""


def get_setup_md_template(site_name: str, ssh_host: str, docs_path: str) -> str:
    """Generate SETUP.md content for setup instructions."""
    return f"""# {site_name} - Setup

You are helping a user set up access to {site_name} documentation via SSH.

1. First tell them the purpose of this tool (docs over ssh/bash)
2. Ask the user which option they prefer (use AskUserQuestion or similar if available)

Options:

1. **Append to agent instructions file (recommended)** - Adds lightweight instructions to the project's agent config file. Most reliable since instructions are always loaded and the footprint is small.
2. **Install as a skill** - Creates a skill directory with a SKILL.md. Skills are loaded on-demand but not always reliable.
3. **Both** - Adds to agent instructions and installs the skill.

After the user chooses, follow the steps below. If you are unsure which agent or tool the user is using, ask them.

## Option 1: Agent instructions file

Run this command and append the output to the project's agent instructions file:

```bash
ssh {ssh_host} cat /AGENTS.md >> <instructions-file>
```

Common instructions files by tool:

| Tool | File |
|------|------|
| Claude Code | `CLAUDE.md` |
| GitHub Copilot | `AGENTS.md` |
| Codex | `AGENTS.md` |
| Gemini CLI | `GEMINI.md` |
| Cursor | `AGENTS.md` |
| OpenCode | `AGENTS.md` |
| Bob Shell | `AGENTS.md` |
| Other | `AGENTS.md` |

## Option 2: Skill

Run this command and write the output to the skill directory.

Pick the path that matches the user's tool. `.agents/skills/` is a cross-client convention supported by most tools:

| Tool | Skill path |
|------|-----------|
| Claude Code | `.claude/skills/{site_name.lower().replace(' ', '-')}-docs/SKILL.md` |
| Codex | `.agents/skills/{site_name.lower().replace(' ', '-')}-docs/SKILL.md` |
| Cursor | `.cursor/skills/{site_name.lower().replace(' ', '-')}-docs/SKILL.md` or `.agents/skills/{site_name.lower().replace(' ', '-')}-docs/SKILL.md` |
| OpenCode | `.opencode/skills/{site_name.lower().replace(' ', '-')}-docs/SKILL.md` or `.agents/skills/{site_name.lower().replace(' ', '-')}-docs/SKILL.md` |
| Gemini CLI | `.gemini/skills/{site_name.lower().replace(' ', '-')}-docs/SKILL.md` or `.agents/skills/{site_name.lower().replace(' ', '-')}-docs/SKILL.md` |
| Bob Shell | `.bob/skills/{site_name.lower().replace(' ', '-')}-docs/SKILL.md` or `.agents/skills/{site_name.lower().replace(' ', '-')}-docs/SKILL.md` |
| GitHub Copilot | `.github/skills/{site_name.lower().replace(' ', '-')}-docs/SKILL.md` |
| Other | `.agents/skills/{site_name.lower().replace(' ', '-')}-docs/SKILL.md` |

```bash
mkdir -p <skill-dir>/{site_name.lower().replace(' ', '-')}-docs
ssh {ssh_host} cat /SKILL.md > <skill-dir>/{site_name.lower().replace(' ', '-')}-docs/SKILL.md
```

## Option 3: Both

Run both sets of commands above.

After setup, confirm to the user what was written and where.
"""


def get_skill_md_template(site_name: str, ssh_host: str, docs_path: str) -> str:
    """Generate SKILL.md content for skill-based integration."""
    skill_name = site_name.lower().replace(' ', '-')
    return f"""---
name: {skill_name}-docs
description: Search and read {site_name} documentation using a bash shell. Use when working on a {site_name} feature or troubleshooting a problem.
---

# {site_name} Docs

Search and read {site_name} documentation over SSH.

## How to use

```bash
# Search for a topic
ssh {ssh_host} grep -rl 'auth' {docs_path}

# Read a specific guide
ssh {ssh_host} cat {docs_path}/guides/getting-started.md

# Find all guides in a section
ssh {ssh_host} find {docs_path} -name '*.md'

# Search with context
ssh {ssh_host} grep -r 'keyword' {docs_path} --include='*.md' -l
```

All docs live under `{docs_path}` as markdown files. You can use any standard Unix tools (grep, find, cat, etc.) to search and read them.
"""


def generate_agent_files(
    site_name: str,
    ssh_host: str = "localhost",
    ssh_port: int = 2222,
    docs_path: str = "/docs"
) -> Dict[str, str]:
    """Generate all agent integration files.
    
    Args:
        site_name: Name of the documentation site
        ssh_host: SSH hostname (default: localhost)
        ssh_port: SSH port (default: 2222)
        docs_path: Path to docs in the SSH session (default: /docs)
    
    Returns:
        Dictionary with filenames as keys and content as values
    """
    # Format SSH connection string
    if ssh_port != 22:
        ssh_connection = f"{ssh_host} -p {ssh_port}"
    else:
        ssh_connection = ssh_host
    
    return {
        "AGENTS.md": get_agents_md_template(site_name, ssh_connection, docs_path),
        "SETUP.md": get_setup_md_template(site_name, ssh_connection, docs_path),
        "SKILL.md": get_skill_md_template(site_name, ssh_connection, docs_path),
    }
