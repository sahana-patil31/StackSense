from typing import Any


class ContextBuilder:
    def __init__(self, max_evidence: int = 8, max_history: int = 6, max_chars: int = 6000):
        self.max_evidence, self.max_history, self.max_chars = max_evidence, max_history, max_chars

    def build(self, question: str, evidence: list[dict[str, Any]], history: list[dict[str, str]]) -> dict[str, Any]:
        selected, chars = [], 0
        for item in evidence[:self.max_evidence]:
            content = item["content"][: max(0, self.max_chars - chars)]
            if not content:
                break
            selected.append({**item, "content": content})
            chars += len(content)
        return {"question": question, "evidence": selected, "history": history[-self.max_history:]}
