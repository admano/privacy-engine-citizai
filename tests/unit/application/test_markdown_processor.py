from collections.abc import Callable

from privacy_engine.application.markdown_processor import MarkdownProcessor


class UppercaseMarkdownProcessor:
    def transform_text(
        self,
        markdown: str,
        transform: Callable[[str], str],
    ) -> str:
        return transform(markdown)


def use_processor(
    processor: MarkdownProcessor,
    markdown: str,
    transform: Callable[[str], str],
) -> str:
    return processor.transform_text(markdown, transform)


def test_processor_contract_accepts_structural_implementation() -> None:
    processor = UppercaseMarkdownProcessor()

    result = use_processor(
        processor,
        "hello",
        lambda text: text.upper(),
    )

    assert result == "HELLO"


def test_processor_contract_delegates_transformation_to_caller() -> None:
    processor = UppercaseMarkdownProcessor()
    received: list[str] = []

    def transform(text: str) -> str:
        received.append(text)
        return f"[{text}]"

    result = use_processor(processor, "content", transform)

    assert received == ["content"]
    assert result == "[content]"
