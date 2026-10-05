from uuid import uuid4

from privacy_engine.application.markdown_models import (
    MarkdownAnonymizationResult,
    MarkdownDocument,
)
from privacy_engine.application.models import AnonymizationMapping
from privacy_engine.domain.entities import PIIEntity


def test_markdown_document_holds_filename_and_content() -> None:
    document = MarkdownDocument(
        filename="notes.md",
        content="# Hello",
    )

    assert document.filename == "notes.md"
    assert document.content == "# Hello"


def test_markdown_document_is_frozen() -> None:
    document = MarkdownDocument(
        filename="notes.md",
        content="# Hello",
    )

    try:
        document.filename = "other.md"  # type: ignore[misc]
    except AttributeError:
        pass
    else:
        raise AssertionError(
            "MarkdownDocument should be immutable"
        )


def test_markdown_anonymization_result_holds_all_fields() -> None:
    document_id = uuid4()

    entity = PIIEntity(
        entity_type="PERSON",
        value="Adam",
        start=0,
        end=4,
    )

    mapping = AnonymizationMapping(
        entity_type="PERSON",
        original_value="Adam",
        replacement_value="[PERSON_001]",
    )

    result = MarkdownAnonymizationResult(
        document_id=document_id,
        filename="notes.md",
        language="en",
        safe_markdown="[PERSON_001]",
        is_safe_for_ai=False,
        entity_count=1,
        entities=(entity,),
        mappings=(mapping,),
    )

    assert result.document_id == document_id
    assert result.filename == "notes.md"
    assert result.language == "en"
    assert result.safe_markdown == "[PERSON_001]"
    assert result.is_safe_for_ai is False
    assert result.entity_count == 1
    assert result.entities == (entity,)
    assert result.mappings == (mapping,)


def test_markdown_anonymization_result_is_frozen() -> None:
    result = MarkdownAnonymizationResult(
        document_id=uuid4(),
        filename="notes.md",
        language="en",
        safe_markdown="Hello",
        is_safe_for_ai=True,
        entity_count=0,
        entities=(),
        mappings=(),
    )

    try:
        result.entity_count = 5  # type: ignore[misc]
    except AttributeError:
        pass
    else:
        raise AssertionError(
            "MarkdownAnonymizationResult should be immutable"
        )
