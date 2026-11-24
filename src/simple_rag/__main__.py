"""Entry point for the simple_rag MCP server.

Usage:
    python -m simple_rag
"""

import sys
from pathlib import Path

# Ensure the package root is on the path (for development)
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from simple_rag.config import AppConfig
from simple_rag.mcp_server import create_mcp_server


def main() -> None:
    """Start the MCP server."""
    config = AppConfig.from_env()
    server = create_mcp_server(config)
    server.run(
        transport="http",
        host=config.mcp.host,
        port=config.mcp.port,
    )


if __name__ == "__main__":
    main()
