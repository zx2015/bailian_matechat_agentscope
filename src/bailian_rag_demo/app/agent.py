"""Local terminal debug loop for developers.

Both local development and the Bailian-hosted runtime now share the exact
same AgentScope-based agent stack (`bailian_rag_demo.app.runtime_agent`).
This module simply wires that agent to stdin/stdout so it can be exercised
without a full HTTP round-trip while iterating on prompts / RAG behavior.

Usage:
    python -m bailian_rag_demo.app.agent
"""
import asyncio
import logging

from bailian_rag_demo.app.runtime_agent import RuntimeAgent
from bailian_rag_demo.config import load_settings
from bailian_rag_demo.rag.bailian_kb import BaiLianKB

logger = logging.getLogger(__name__)


async def _chat_loop() -> None:
    settings = load_settings()
    kb = BaiLianKB(settings)
    agent = RuntimeAgent(settings=settings)
    session_id = "local-debug"

    print("Bailian RAG local debug chat. Type 'exit' to quit.")
    while True:
        try:
            query = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not query or query.lower() in {"exit", "quit"}:
            break
        answer, usage = await agent.run_async(query, kb, session_id=session_id)
        print(f"Assistant: {answer}")
        if usage:
            print(f"  (usage: {usage})")


def main() -> None:
    asyncio.run(_chat_loop())


if __name__ == "__main__":
    main()
