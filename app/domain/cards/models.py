import uuid
from enum import StrEnum
from sqlalchemy import ForeignKey, String, Text, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base, TimestampMixin


class CardPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Card(Base, TimestampMixin):
    __tablename__ = "cards"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    priority: Mapped[CardPriority] = mapped_column(
        default=CardPriority.MEDIUM, nullable=False
    )
    due_date: Mapped[str | None] = mapped_column(DateTime(timezone=True))

    list_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lists.id", ondelete="CASCADE"), nullable=False
    )
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    # Relationships
    list: Mapped["List"] = relationship(back_populates="cards")
    assignee: Mapped["User | None"] = relationship(back_populates="assigned_cards")
    labels: Mapped[list["Label"]] = relationship(
        secondary="card_labels", back_populates="cards"
    )
    history: Mapped[list["CardHistory"]] = relationship(
        back_populates="card", cascade="all, delete-orphan"
    )


class CardHistory(Base):
    __tablename__ = "cards_history"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    card_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cards.id", ondelete="CASCADE"), nullable=False
    )
    changed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    field_changed: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text)
    new_value: Mapped[str | None] = mapped_column(Text)
    changed_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    card: Mapped["Card"] = relationship(back_populates="history")
    author: Mapped["User | None"] = relationship()