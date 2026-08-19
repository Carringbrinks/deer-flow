"""Configuration for the RAG (retrieval-augmented generation) middleware.

The harness does not implement retrieval itself: it calls an operator-provided
search-completion HTTP service and injects the streamed answer plus references
into the model context as hidden, untrusted data. See
``deerflow.agents.middlewares.rag_middleware`` for the request/response
contract and the injection semantics.

Endpoint contract::

    POST {base_url}/api/v1/searches/{search_id}/completions
    Authorization: Bearer <api_key>
    Body: {"question": "...", "kb_ids": ["..."]}
    Response: SSE stream of ``data: {"code":0,"message":"","data":{"answer":"...","reference":{...}}}``
              terminated by ``data: {"code":0,"message":"","data":true}``.
"""

import logging

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class RagConfig(BaseModel):
    """Search-completion service configuration for the RAG middleware.

    ``enabled`` gates whether the middleware is even attached. All network
    fields are only read when the middleware performs a retrieval; a retrieval
    failure always fails open (the model call proceeds without RAG context).
    """

    enabled: bool = Field(
        default=False,
        description="Whether to enable the RAG middleware and call the search-completion service.",
    )
    base_url: str = Field(
        default="",
        description=("Base URL of the RAG service (e.g. http://rag-service:8080). The request is POSTed to base_url + /api/v1/searches/{search_id}/completions."),
    )
    search_id: str = Field(
        default="",
        description="The ID of the search app (path parameter in the completion endpoint).",
    )
    kb_ids: list[str] = Field(
        default_factory=list,
        description=("Optional fallback dataset IDs sent in the request body. Used only when the search app config does not already define kb_ids."),
    )
    api_key: str | None = Field(
        default=None,
        description="Login token sent as 'Authorization: Bearer <api_key>' on every request.",
    )
    timeout_seconds: float = Field(
        default=60.0,
        ge=1.0,
        le=300.0,
        description="Per-request timeout (seconds) for the streaming completion service.",
    )
    max_context_chars: int = Field(
        default=6000,
        ge=0,
        description=("Character budget for the injected context block. The answer/references are truncated to fit. 0 disables truncation."),
    )

    @property
    def url(self) -> str:
        """Full completion endpoint URL."""
        base = self.base_url.rstrip("/")
        return f"{base}/api/v1/searches/{self.search_id}/completions"


# Global configuration instance.
_rag_config: RagConfig = RagConfig()


def get_rag_config() -> RagConfig:
    """Get the current RAG configuration singleton.

    Mirrors ``get_memory_config``: when ``get_app_config()`` has already been
    loaded, a reload is triggered first so hot-reloadable ``rag.*`` edits are
    picked up; otherwise the in-memory singleton (module defaults) is returned
    to avoid loading a config file as a side effect of first access.
    """
    from .app_config import _app_config, get_app_config

    if _app_config is not None:
        try:
            get_app_config()
        except Exception:
            logger.warning(
                "Failed to reload app config from get_rag_config(); falling back to cached rag config.",
                exc_info=True,
            )
    return _rag_config


def set_rag_config(config: RagConfig) -> None:
    """Set the RAG configuration singleton (used by tests)."""
    global _rag_config
    _rag_config = config


def load_rag_config_from_dict(config_dict: dict) -> None:
    """Load RAG configuration from a dictionary (called by AppConfig reload)."""
    global _rag_config
    _rag_config = RagConfig(**(config_dict or {}))
