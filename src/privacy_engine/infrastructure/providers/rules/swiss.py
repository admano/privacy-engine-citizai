import re

from stdnum import iban
from stdnum.ch import ssn, uid

from privacy_engine.infrastructure.providers.rules.engine import Rule


def swiss_rules() -> tuple[Rule, ...]:
    return (
        Rule(
            entity_type="CH_AHV",
            pattern=re.compile(r"\b756[.\s]?\d{4}[.\s]?\d{4}[.\s]?\d{2}\b"),
            base_score=0.75,
            validator=ssn.is_valid,
            context_words={
                "de": ("ahv", "ahv nummer", "versichertennummer"),
                "fr": ("avs", "numéro avs", "numéro assuré"),
                "it": ("avs", "numero avs", "numero assicurato"),
                "en": ("ahv", "ahv number", "insurance number"),
            },
        ),
        Rule(
            entity_type="CH_IBAN",
            pattern=re.compile(r"\bCH\d{2}(?:\s?[A-Z0-9]){17}\b"),
            base_score=0.8,
            validator=iban.is_valid,
            context_words={
                "de": ("iban", "konto", "kontonummer", "bankkonto"),
                "fr": ("iban", "compte", "compte bancaire"),
                "it": ("iban", "conto", "conto bancario"),
                "en": ("iban", "bank account", "account"),
            },
        ),
        Rule(
            entity_type="CH_UID",
            pattern=re.compile(r"\bCHE[-.\s]?\d{3}[.\s]?\d{3}[.\s]?\d{3}\b"),
            base_score=0.7,
            validator=uid.is_valid,
            context_words={
                "de": ("uid", "uid nr", "unternehmensnummer", "mwst"),
                "fr": ("ide", "numéro ide", "tva"),
                "it": ("ide", "numero ide", "iva"),
                "en": ("uid", "company number", "vat"),
            },
        ),
        Rule(
            entity_type="CH_PHONE",
            pattern=re.compile(
                r"(?<!\w)(?:\+41|0041|0)\s?\d{2}"
                r"(?:[\s.-]?\d{3})(?:[\s.-]?\d{2})(?:[\s.-]?\d{2})(?!\w)"
            ),
            base_score=0.45,
            context_words={
                "de": ("telefon", "telefonnummer", "handy", "mobil"),
                "fr": ("téléphone", "telephone", "portable"),
                "it": ("telefono", "cellulare"),
                "en": ("phone", "phone number", "mobile"),
            },
        ),
    )
