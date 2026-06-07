"""AWS Pricing Calculator estimate generator — MCP server, REST API and CLI."""

__version__ = "1.1.0"

from .core import create_estimate, format_result  # noqa: F401

__all__ = ["create_estimate", "format_result", "__version__"]
