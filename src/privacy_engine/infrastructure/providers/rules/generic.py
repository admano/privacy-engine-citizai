import ipaddress
import re

from stdnum import luhn

from privacy_engine.infrastructure.providers.rules.engine import Rule


def _is_valid_credit_card(value: str) -> bool:
    normalized = value.replace(" ", "").replace("-", "")
    return luhn.is_valid(normalized)


def _is_valid_ip_address(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return False

    return True


def default_rules() -> tuple[Rule, ...]:
    return (
        Rule(
            entity_type="EMAIL",
            pattern=re.compile(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
            ),
            base_score=0.95,
        ),
        Rule(
            entity_type="CREDIT_CARD",
            pattern=re.compile(
                r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)"
            ),
            base_score=0.9,
            validator=_is_valid_credit_card,
        ),
        Rule(
            entity_type="IP_ADDRESS",
            pattern=re.compile(
                r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])"
            ),
            base_score=0.9,
            validator=_is_valid_ip_address,
        ),
        Rule(
            entity_type="URL",
            pattern=re.compile(
                r"\bhttps?://[^\s<>()\[\]{}\"']*[A-Za-z0-9/#]"
            ),
            base_score=0.9,
        ),
    )
