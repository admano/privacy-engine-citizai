import uuid

from sqlalchemy import BigInteger, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from privacy_engine.infrastructure.database.base import Base


class AnonymizationMappingModel(Base):
    __tablename__ = "anonymization_mapping"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        nullable=False,
        index=True,
    )

    entity_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    original_value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    replacement_value: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )