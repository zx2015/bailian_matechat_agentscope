"""Local AgentScope agent for developer debugging.

Not used inside the Bailian runtime. Provides a familiar ReAct-style entry
point for iterating on prompts / RAG behavior without redeploying.
"""
import logging

from bailian_rag_demo.config import Settings
from bailian_rag_demo.rag.base import KnowledgeBase

logger = logging.getLogger(__name__)


class LocalAgent:
    """Thin wrapper that mirrors RuntimeAgent's contract using AgentScope."""

    def __init__(self, settings: Settings, kb: KnowledgeBase) -> None:
        self._settings = settings
        self._kb = kb

    def chat(self, query: str) -> str:
        hits = self._kb.retrieve(query, top_k=self._settings.BAILIAN_RAG_TOP_K)
        context = "\n".join(f"[{h.source}] {h.content}" for h in hits) or "(none)"
        try:
            import agentscope  # type: ignore
        except ImportError:
            logger.warning("agentscope not installed; falling back to plain echo")
            return f"[local-fallback] ctx={context!r} query={query!r}"
        # Minimal AgentScope usage: print context and return a placeholder.
        # Real implementations can swap in ReActAgent / etc.
        logger.info("agentscope version: %s", getattr(agentscope, "__version__", "?"))
        return f"[agentscope] ctx-len={len(context)} q={query}"