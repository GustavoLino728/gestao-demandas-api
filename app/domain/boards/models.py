import uuid
from datetime import datetime
from enum import StrEnum
from sqlalchemy import String, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base
from app.domain.lists.models import List  # adicionar import

class Board(Base):
    __tablename__ = "boards"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    owner: Mapped["User"] = relationship("User", back_populates="boards")
    lists: Mapped[list["List"]] = relationship("List", back_populates="board", cascade="all, delete-orphan", order_by="List.position")
    members: Mapped[list["BoardMember"]] = relationship("BoardMember", back_populates="board", cascade="all, delete-orphan")

class BoardRole(StrEnum):
    VIEWER = "viewer"
    MEMBER = "member"
    ADMIN  = "admin"

class BoardMember(Base):
    __tablename__ = "board_members"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    board_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("boards.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[BoardRole] = mapped_column(default=BoardRole.MEMBER, nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    board: Mapped["Board"] = relationship("Board", back_populates="members")
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        UniqueConstraint("board_id", "user_id", name="uq_board_member"),
    )