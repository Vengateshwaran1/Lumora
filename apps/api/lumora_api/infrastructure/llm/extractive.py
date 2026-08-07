"""Template-based, non-generative ChatProvider — no LLM call at all.

Formats retrieved chunks into a citation-first summary instead of
generating prose. Keeps `/chat` functional with zero setup (the offline
default); switch to OllamaChatProvider for real generated answers.
"""

from lumora_api.domain.retrieval import RetrievedChunk
from lumora_api.infrastructure.llm.base import ChatProvider


class ExtractiveChatProvider(ChatProvider):
    async def generate_answer(self, question: str, chunks: list[RetrievedChunk]) -> str:
        if not chunks:
            return f"No relevant code was found for: {question!r}"

        lines = [f"Found {len(chunks)} relevant location(s) for: {question!r}", ""]
        for chunk in chunks:
            label = chunk.symbol or chunk.kind
            lines.append(
                f"- {label} ({chunk.kind}) in {chunk.file_path}:{chunk.start_line}-{chunk.end_line}"
            )
        return "\n".join(lines)
