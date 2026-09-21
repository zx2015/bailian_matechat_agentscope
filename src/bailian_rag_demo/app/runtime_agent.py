"""Cloud-runtime agent: AgentScope ReAct orchestration with Bailian RAG context.

This is the canonical execution path used both locally and inside the
Bailian-hosted runtime. It uses `agentscope`'s `ReActAgent` bound to a
`dashscope`-backed chat model, so the same agent stack runs everywhere
(no separate "cloud-only" implementation is needed anymore).

Retrieval still goes through the `KnowledgeBase` abstraction (`BaiLianKB` in
stage 1); results are folded into the user turn's content before being
handed to AgentScope, keeping the RAG backend swappable without touching the
agent orchestration.
"""
import asyncio
import logging
from typing import Any, Dict, Optional, Tuple

from bailian_rag_demo.config import Settings
from bailian_rag_demo.rag.base import KnowledgeBase

logger = logging.getLogger(__name__)

try:
    from agentscope.agent import ReActAgent
    from agentscope.formatter import DashScopeChatFormatter
    from agentscope.message import Msg
    from agentscope.model import DashScopeChatModel
except ImportError:  # pragma: no cover
    ReActAgent = None  # type: ignore
    DashScopeChatFormatter = None  # type: ignore
    Msg = None  # type: ignore
    DashScopeChatModel = None  # type: ignore


SYSTEM_PROMPT = (
    "You are a helpful assistant for the Bailian RAG demo. Answer the "
    "user's question using the provided reference material when relevant. "
    "If no reference material is given, answer from general knowledge."
)

_DEFAULT_SESSION_KEY = "__default__"


class _UsageTrackingModel:
    """Thin wrapper around `DashScopeChatModel` that records the token usage
    of the most recent call, since `ReActAgent` does not surface it."""

    def __init__(self, model: Any) -> None:
        self._model = model
        self.last_usage: Optional[Dict[str, Any]] = None

    def __getattr__(self, item: str) -> Any:
        return getattr(self._model, item)

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        response = await self._model(*args, **kwargs)
        usage = getattr(response, "usage", None)
        if usage is not None:
            self.last_usage = {
                "input_tokens": getattr(usage, "input_tokens", None),
                "output_tokens": getattr(usage, "output_tokens", None),
            }
        return response


class RuntimeAgent:
    """AgentScope-backed agent shared by local dev and the Bailian runtime.

    Maintains one `ReActAgent` (with its own in-memory conversation history)
    per `session_id` so multi-turn chats keep context across `/process`
    calls within the same running process.
    """

    def __init__(self, settings: Settings, model_name: str = "qwen-turbo") -> None:
        if ReActAgent is None:
            raise ImportError(
                "agentscope is required for RuntimeAgent; install via "
                "`pip install agentscope`"
            )
        self._settings = settings
        self._model_name = model_name
        self._sessions: Dict[str, Tuple[ReActAgent, _UsageTrackingModel]] = {}

    def _get_agent(self, session_id: Optional[str]) -> Tuple["ReActAgent", _UsageTrackingModel]:
        key = session_id or _DEFAULT_SESSION_KEY
        if key not in self._sessions:
            model = _UsageTrackingModel(
                DashScopeChatModel(
                    model_name=self._model_name,
                    api_key=self._settings.DASHSCOPE_API_KEY,
                    stream=False,
                )
            )
            agent = ReActAgent(
                name="bailian-rag-assistant",
                sys_prompt=SYSTEM_PROMPT,
                model=model,
                formatter=DashScopeChatFormatter(),
            )
            self._sessions[key] = (agent, model)
        return self._sessions[key]

    @staticmethod
    def _build_user_content(query: str, context: str) -> str:
        if not context:
            return query
        return (
            f"[参考资料]\n{context}\n\n[用户问题]\n{query}"
        )

    async def run_async(
        self,
        query: str,
        kb: KnowledgeBase,
        session_id: Optional[str] = None,
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        hits = kb.retrieve(query, top_k=self._settings.BAILIAN_RAG_TOP_K)
        context = "\n---\n".join(h.content for h in hits) if hits else ""

        agent, model = self._get_agent(session_id)
        user_msg = Msg(
            name="user",
            role="user",
            content=self._build_user_content(query, context),
        )
        reply = await agent(user_msg)
        text = reply.get_text_content() or ""
        return text, model.last_usage

    def run(
        self,
        query: str,
        kb: KnowledgeBase,
        session_id: Optional[str] = None,
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Synchronous convenience wrapper (used by local debugging/tests)."""
        return asyncio.run(self.run_async(query, kb, session_id=session_id))