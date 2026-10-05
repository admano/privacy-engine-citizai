from collections.abc import Callable
from typing import Protocol


class MarkdownProcessor(Protocol):
    def transform_text(
        self,
        markdown: str,
        transform: Callable[[str], str],
    ) -> str:
        ...
