from __future__ import annotations

from typing import Optional


class AgentError(Exception):
    """Base exception for agent-related failures."""

    def __init__(self, message: str, *, detail: Optional[str] = None) -> None:
        super().__init__(message)
        self.detail = detail


class ConfigurationError(AgentError):
    """Raised when required configuration or environment values are missing."""


class ExternalServiceError(AgentError):
    """Raised when an external dependency (RAG, LLM, HTTP API) fails."""


class ToolExecutionError(AgentError):
    """Raised when an MCP tool cannot complete its execution."""


class ConversationStateError(AgentError):
    """Raised when expected data is missing from the agent conversation state."""


