from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Table, Column, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

PERSON_COLORS = [
    "#e05252", "#e0a052", "#d9c852", "#8fd952", "#52d9a0",
    "#52c3d9", "#5273d9", "#8a52d9", "#d952c3", "#d95285",
]

game_session_players = Table(
    "game_session_players",
    Base.metadata,
    Column("session_id", ForeignKey("game_sessions.id", ondelete="CASCADE"), primary_key=True),
    Column("person_id", ForeignKey("people.id", ondelete="CASCADE"), primary_key=True),
)


class Person(Base):
    __tablename__ = "people"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    attendances: Mapped[list["Attendance"]] = relationship(
        back_populates="person", cascade="all, delete-orphan"
    )
    inventory_items: Mapped[list["InventoryItem"]] = relationship(
        back_populates="person", cascade="all, delete-orphan"
    )
    game_sessions: Mapped[list["GameSession"]] = relationship(
        secondary=game_session_players, back_populates="players"
    )


class Attendance(Base):
    """A continuous block of time a person will be present at the LAN."""

    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(primary_key=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"))
    start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    person: Mapped["Person"] = relationship(back_populates="attendances")


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    sessions: Mapped[list["GameSession"]] = relationship(
        back_populates="game", cascade="all, delete-orphan", order_by="GameSession.start"
    )


class GameSession(Base):
    """A scheduled block of time to play a specific game."""

    __tablename__ = "game_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id", ondelete="CASCADE"))
    start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    game: Mapped["Game"] = relationship(back_populates="sessions")
    players: Mapped[list["Person"]] = relationship(
        secondary=game_session_players, back_populates="game_sessions"
    )


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    category: Mapped[str] = mapped_column(String(64), default="Other", nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    person: Mapped["Person"] = relationship(back_populates="inventory_items")
