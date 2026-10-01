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

meal_attendees = Table(
    "meal_attendees",
    Base.metadata,
    Column("meal_id", ForeignKey("meals.id", ondelete="CASCADE"), primary_key=True),
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
    meals_eating: Mapped[list["Meal"]] = relationship(
        secondary=meal_attendees, back_populates="attendees"
    )
    meals_cooking: Mapped[list["Meal"]] = relationship(
        back_populates="cook", foreign_keys="Meal.cook_id"
    )
    meals_cleaning: Mapped[list["Meal"]] = relationship(
        back_populates="cleaner", foreign_keys="Meal.cleaner_id"
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


class Meal(Base):
    """A planned meal: when it's happening, who's cooking, who's eating, who's cleaning up."""

    __tablename__ = "meals"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    cook_id: Mapped[int | None] = mapped_column(
        ForeignKey("people.id", ondelete="SET NULL"), nullable=True
    )
    cleaner_id: Mapped[int | None] = mapped_column(
        ForeignKey("people.id", ondelete="SET NULL"), nullable=True
    )

    cook: Mapped["Person | None"] = relationship(
        back_populates="meals_cooking", foreign_keys=[cook_id]
    )
    cleaner: Mapped["Person | None"] = relationship(
        back_populates="meals_cleaning", foreign_keys=[cleaner_id]
    )
    attendees: Mapped[list["Person"]] = relationship(
        secondary=meal_attendees, back_populates="meals_eating"
    )
