"""Cloud-runtime agent: assembles prompt with RAG context, calls LLM via dashscope.

This is the canonical execution path used inside the Bailian-hosted runtime
(no AgentScope dependency required).
"""
import logging
from typing import Optional, Tuple, Dict, Any

from bailian_rag_demo.config import Settings
from bailian_rag_demo.rag.base import KnowledgeBase

logger = logging.getLogger(__name__)

try:
    import dashscope
except ImportError:  # pragma: no cover
    dashscope = None  # type: ignore


SYSTEM_PROMPT_TEMPLATE = (
    "You are a helpful assistant. Use the following context to answer the user's "
    "question. If the context is empty, answer from general knowledge.\n\n"
    "Context:\n{context}\n"
)


class RuntimeAgent:
    def __init__(self, settings: Settings, kb: KnowledgeBase) -> None:
        if dashscope is None:
            raise ImportError("dashscope required for RuntimeAgent")
        dashscope.api_key = settings.DASHSCOPE_API_KEY
        self._settings = settings
        self._kb = kb

    def run(self, query: str, session_id: Optional[str] = None) -> Tuple[str, Optional[Dict[str, Any]]]:
        hits = self._kb.retrieve(query, top_k=self._settings.BAILIAN_RAG_TOP_K)
        context = "\n---\n".join(h.content for h in hits) if hits else "(no context)"
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)
        prompt = f"{system_prompt}\nUser: {query}"

        response = dashscope.Generation.call(
            model="qwen-turbo",
            prompt=prompt,
            result_format="message",
        )
        return self._extract_response(response)

    @classmethod
    def _extract_response(cls, response) -> Tuple[str, Optional[Dict[str, Any]]]:
        usage: Optional[Dict[str, Any]] = None
        try:
            if isinstance(response, dict):
                usage = response.get("usage")
            elif hasattr(response, "usage"):
                usage = response.usage
        except Exception:
            pass

        text = cls._extract_text(response)
        return text, usage

    @staticmethod
    def _extract_text(response) -> str:
        try:
            output = response["output"] if isinstance(response, dict) else getattr(response, "output", {})
            try:
                choices = output.get("choices") if isinstance(output, dict) else getattr(output, "choices", None)
                if choices:
                    first = choices[0]
                    msg = first.get("message") if isinstance(first, dict) else getattr(first, "message", None)
                    return msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")
                return output.get("text", "") if isinstance(output, dict) else getattr(output, "text", "")
            except (KeyError, IndexError, TypeError, AttributeError):
                return output.get("text", "") if isinstance(output, dict) else getattr(output, "text", "")
        except (KeyError, TypeError, AttributeError) as exc:
            logger.warning("Unexpected dashscope response shape: %s; err=%s", response, exc)
            return ""