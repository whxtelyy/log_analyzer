from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy import String, DateTime, Text, Index
from datetime import datetime
from typing import Optional

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(20), unique=True)
    password: Mapped[str] = mapped_column(String(20))

    def __repr__(self):
        return f'id = {self.id!r}, login= {self.username!r}'

class LogDB(Base):
    __tablename__ = "log"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    level: Mapped[str] = mapped_column(String(20))
    service: Mapped[str] = mapped_column(String(100))
    message: Mapped[str] = mapped_column(String())
    metadata_json: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)

    __table_args__ = (
        Index("index_log_timestamp", "timestamp"),
        Index("index_log_level", "level"),
        Index("index_log_service", "service"),
        Index("idx_log_level_service", "level", "service"),
    )

    def __repr__(self):
        return (f'id = {self.id!r}, timestamp = {self.timestamp!r},'
                f' level = {self.level!r}, service = {self.service!r}, message = {self.message!r}'
        )