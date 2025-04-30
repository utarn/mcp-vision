import logging
import sys

from mcp_vision.server import mcp

logger = logging.getLogger(__name__)


def main():
    try:
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        sys.exit(1)


__all__ = ["main"]
