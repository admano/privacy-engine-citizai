from privacy_engine.infrastructure.markdown.regex_markdown_processor import (
    RegexMarkdownProcessor,
)


def _mark(text: str) -> str:
    return f"<<{text}>>"


def _redact_name(text: str) -> str:
    return text.replace("John Smith", "[PERSON_001]")


def test_empty_markdown_returns_empty_string() -> None:
    processor = RegexMarkdownProcessor()

    assert processor.transform_text("", _mark) == ""


def test_plain_paragraph_is_fully_transformed() -> None:
    processor = RegexMarkdownProcessor()

    result = processor.transform_text("Hello world", _mark)

    assert result == "<<Hello world>>"


def test_heading_marker_is_preserved_while_text_is_transformed() -> None:
    processor = RegexMarkdownProcessor()

    result = processor.transform_text(
        "# Customer\n\nName: John Smith",
        _redact_name,
    )

    assert result == "# Customer\n\nName: [PERSON_001]"


def test_list_and_blockquote_markers_survive_transformation() -> None:
    processor = RegexMarkdownProcessor()

    markdown = "- Contact: John Smith\n> Note: John Smith"

    result = processor.transform_text(markdown, _redact_name)

    assert result == "- Contact: [PERSON_001]\n> Note: [PERSON_001]"


def test_table_cells_survive_transformation() -> None:
    processor = RegexMarkdownProcessor()

    markdown = "| Name | Role |\n| --- | --- |\n| John Smith | Owner |"

    result = processor.transform_text(markdown, _redact_name)

    assert (
        result
        == "| Name | Role |\n| --- | --- |\n| [PERSON_001] | Owner |"
    )


def test_fenced_code_block_is_not_transformed() -> None:
    processor = RegexMarkdownProcessor()

    markdown = "Before\n\n```python\nJohn Smith\n```\n\nAfter"

    result = processor.transform_text(markdown, _mark)

    assert "```python\nJohn Smith\n```" in result
    assert "<<" not in result.split("```python")[1].split("```")[0]
    assert "Before" in result
    assert "After" in result


def test_fenced_code_block_without_closing_fence_is_protected_to_eof() -> (
    None
):
    processor = RegexMarkdownProcessor()

    markdown = "Intro\n\n```\nunclosed code\nstill code"

    result = processor.transform_text(markdown, _mark)

    assert "unclosed code\nstill code" in result
    assert "<<unclosed" not in result


def test_tilde_fence_is_protected() -> None:
    processor = RegexMarkdownProcessor()

    markdown = "~~~\nJohn Smith\n~~~"

    result = processor.transform_text(markdown, _redact_name)

    assert result == markdown


def test_inline_code_span_is_not_transformed() -> None:
    processor = RegexMarkdownProcessor()

    markdown = "Run `John Smith` as a literal command"

    result = processor.transform_text(markdown, _redact_name)

    assert "`John Smith`" in result
    assert "[PERSON_001]" not in result


def test_inline_link_label_is_transformed_but_destination_is_not() -> None:
    processor = RegexMarkdownProcessor()

    markdown = "[Contact John Smith](https://example.com/profile/john)"

    result = processor.transform_text(markdown, _redact_name)

    assert result == (
        "[Contact [PERSON_001]](https://example.com/profile/john)"
    )


def test_image_alt_text_is_transformed_but_destination_is_not() -> None:
    processor = RegexMarkdownProcessor()

    markdown = "![Photo of John Smith](https://example.com/john.png)"

    result = processor.transform_text(markdown, _redact_name)

    assert result == (
        "![Photo of [PERSON_001]](https://example.com/john.png)"
    )


def test_link_destination_with_nested_parentheses_is_preserved() -> None:
    processor = RegexMarkdownProcessor()

    markdown = (
        "[Contact John Smith]"
        "(https://en.wikipedia.org/wiki/Example_(disambiguation))"
    )

    result = processor.transform_text(markdown, _redact_name)

    assert (
        "https://en.wikipedia.org/wiki/Example_(disambiguation)"
        in result
    )
    assert "[PERSON_001]" in result


def test_autolink_is_not_transformed() -> None:
    processor = RegexMarkdownProcessor()

    markdown = "See <https://example.com/john-smith> for details"

    result = processor.transform_text(markdown, _redact_name)

    assert "<https://example.com/john-smith>" in result


def test_email_autolink_is_not_transformed() -> None:
    processor = RegexMarkdownProcessor()

    markdown = "Contact <john.smith@example.com> directly"

    result = processor.transform_text(markdown, _mark)

    assert "<john.smith@example.com>" in result


def test_reference_style_link_identifier_is_protected() -> None:
    processor = RegexMarkdownProcessor()

    markdown = "[Contact John Smith][profile]\n\n[profile]: https://example.com/john"

    result = processor.transform_text(markdown, _redact_name)

    assert "[Contact [PERSON_001]][profile]" in result
    assert "[profile]: https://example.com/john" in result


def test_reference_definition_line_is_fully_protected() -> None:
    processor = RegexMarkdownProcessor()

    markdown = '[John Smith]: https://example.com "John Smith"'

    result = processor.transform_text(markdown, _redact_name)

    assert result == markdown


def test_multiple_protected_constructs_in_one_document() -> None:
    processor = RegexMarkdownProcessor()

    markdown = (
        "# Customer\n\n"
        "Name: John Smith\n\n"
        "```\n"
        "John Smith\n"
        "```\n\n"
        "Email: `john@example.com`\n\n"
        "[Profile](https://example.com/john)"
    )

    result = processor.transform_text(markdown, _redact_name)

    assert "Name: [PERSON_001]" in result
    assert "```\nJohn Smith\n```" in result
    assert "`john@example.com`" in result
    assert "[Profile](https://example.com/john)" in result


def test_transform_is_called_per_line_not_per_whole_block() -> None:
    processor = RegexMarkdownProcessor()
    received: list[str] = []

    def record(text: str) -> str:
        received.append(text)
        return text

    processor.transform_text(
        "Name: Adam Taoussi\nEmail: adam@example.com",
        record,
    )

    assert received == [
        "Name: Adam Taoussi",
        "Email: adam@example.com",
    ]


def test_transform_never_receives_the_line_terminator() -> None:
    processor = RegexMarkdownProcessor()

    def swallow_everything(text: str) -> str:
        # Simulates a detector whose entity span (incorrectly) covers
        # the rest of the fragment it was given, including any
        # trailing whitespace it might contain.
        return "[REDACTED]"

    result = processor.transform_text(
        "# Heading\n\nParagraph",
        swallow_everything,
    )

    # The blank line separating the heading from the paragraph must
    # survive even though `transform` claims nothing of its own input.
    assert result == "[REDACTED]\n\n[REDACTED]"


def test_transform_receives_only_eligible_fragments() -> None:
    processor = RegexMarkdownProcessor()
    received: list[str] = []

    def record(text: str) -> str:
        received.append(text)
        return text

    markdown = "Before [Label](https://example.com) after ```\ncode\n```"

    processor.transform_text(markdown, record)

    combined = "".join(received)

    assert "https://example.com" not in combined
    assert "code" not in combined
