import re
from collections.abc import Callable

# Fenced code blocks: a line opening with (up to 3 spaces indent then) a
# run of 3+ backticks/tildes, content, then a matching closing fence (or
# end of document if the fence is never closed).
_FENCE_PATTERN = re.compile(
    r"^[ ]{0,3}(`{3,}|~{3,})[^\n]*\n"
    r"(?:.*(?:\n|\Z))*?"
    r"(?:^[ ]{0,3}\1[ \t]*$\n?|\Z)",
    re.MULTILINE,
)

# Inline code spans: a run of backticks, content, then a run of
# backticks of the same length.
_INLINE_CODE_PATTERN = re.compile(
    r"(`+)(.+?)(?<!`)\1(?!`)",
    re.DOTALL,
)

# Autolinks: <scheme:...> or <email@example.com>.
_AUTOLINK_PATTERN = re.compile(
    r"<(?:[a-zA-Z][a-zA-Z0-9+.-]{1,31}:[^\s<>]*|[^\s<>@]+@[^\s<>]+)>"
)

# Reference-link definitions, e.g. `[ref]: https://example.com "title"`.
# The whole line is treated as protected: it is structural/definitional
# rather than human-readable prose, and always carries a destination.
_REFERENCE_DEFINITION_PATTERN = re.compile(
    r"^[ ]{0,3}\[[^\]]*\]:[^\n]*$",
    re.MULTILINE,
)

# The `[ref]` identifier half of a reference-style link `[label][ref]`.
# Only the second bracket is protected; `[label]` remains eligible text.
_REFERENCE_LINK_PATTERN = re.compile(r"(?<=\])\[[^\]]*\]")

# The `(destination "title")` half of an inline link/image
# `[label](destination "title")` / `![alt](destination "title")`.
# Supports one level of nested parentheses inside the destination
# (e.g. Wikipedia-style URLs); destinations are assumed single-line.
_LINK_DESTINATION_PATTERN = re.compile(
    r"(?<=\])\((?:[^()\n]|\([^()\n]*\))*\)"
)

_PROTECTED_PATTERNS = (
    _FENCE_PATTERN,
    _INLINE_CODE_PATTERN,
    _AUTOLINK_PATTERN,
    _REFERENCE_DEFINITION_PATTERN,
    _REFERENCE_LINK_PATTERN,
    _LINK_DESTINATION_PATTERN,
)


class RegexMarkdownProcessor:
    """Markdown-structure-aware text processor.

    Identifies fenced code blocks, inline code spans, link/image
    destinations, autolinks, and reference-link definitions as
    "protected" and leaves them untouched. Every other span of the
    document is treated as eligible human-readable text and is handed,
    verbatim, to the caller-supplied `transform` callback. Because the
    original characters are only ever copied or replaced wholesale by
    `transform`'s return value - never re-rendered from a parsed tree -
    Markdown syntax outside the transformed spans cannot drift.
    """

    def transform_text(
        self,
        markdown: str,
        transform: Callable[[str], str],
    ) -> str:
        if not markdown:
            return markdown

        protected_ranges = self._find_protected_ranges(markdown)

        pieces: list[str] = []
        cursor = 0

        for start, end in protected_ranges:
            eligible = markdown[cursor:start]

            if eligible:
                pieces.append(self._transform_lines(eligible, transform))

            pieces.append(markdown[start:end])
            cursor = end

        tail = markdown[cursor:]

        if tail:
            pieces.append(self._transform_lines(tail, transform))

        return "".join(pieces)

    @staticmethod
    def _transform_lines(
        text: str,
        transform: Callable[[str], str],
    ) -> str:
        # Transforming per source line - rather than the whole eligible
        # span at once - keeps within-line multi-word entities (e.g. a
        # full name) intact while preventing an NER model from merging
        # unrelated adjacent lines (e.g. a heading and the paragraph
        # after it) into a single spurious cross-line entity.
        pieces: list[str] = []

        for line in text.splitlines(keepends=True):
            content, line_ending = (
                RegexMarkdownProcessor._split_line_ending(line)
            )

            # The line terminator itself is never handed to `transform`:
            # NER models occasionally include trailing whitespace in a
            # detected span, which would otherwise let a PII replacement
            # silently swallow the newline and collapse Markdown
            # structure (e.g. a blank line separating two paragraphs).
            pieces.append(transform(content) if content else content)
            pieces.append(line_ending)

        return "".join(pieces)

    @staticmethod
    def _split_line_ending(line: str) -> tuple[str, str]:
        content = line.rstrip("\r\n")
        return content, line[len(content):]

    def _find_protected_ranges(
        self,
        markdown: str,
    ) -> list[tuple[int, int]]:
        spans = [
            match.span()
            for pattern in _PROTECTED_PATTERNS
            for match in pattern.finditer(markdown)
        ]

        return self._merge(spans)

    @staticmethod
    def _merge(
        spans: list[tuple[int, int]],
    ) -> list[tuple[int, int]]:
        if not spans:
            return []

        ordered = sorted(spans)
        merged = [ordered[0]]

        for start, end in ordered[1:]:
            last_start, last_end = merged[-1]

            if start <= last_end:
                merged[-1] = (last_start, max(last_end, end))
            else:
                merged.append((start, end))

        return merged
