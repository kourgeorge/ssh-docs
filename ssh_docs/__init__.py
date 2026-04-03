"""SSH-Docs: Expose documentation via SSH.

Browse your documentation using familiar Unix commands over SSH.
"""

__version__ = "0.1.0"
__author__ = "SSH-Docs Contributors"

from .config import Config, load_config
from .server import SSHDocsServer, run_server
from .shell import SSHDocsShell

__all__ = [
    "Config",
    "load_config",
    "SSHDocsServer",
    "run_server",
    "SSHDocsShell",
]
