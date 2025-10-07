from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy import String, DateTime, Text
from datetime import datetime
from typing import Optional

class Base(DeclarativeBase):
    pass

class LogDB(Base):
    __tablename__ = "log"

    id: Mapped[int] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    level: Mapped[String] = mapped_column(String(20))
    service: Mapped[String] = mapped_column(String(100))
    message: Mapped[String] = mapped_column(String())
    metadata_json: Mapped[Optional[str]] = mapped_column(Text(), nullable=True)

    def __repr__(self):
        return (f'id = {self.id!r}, timestamp = {self.timestamp!r},'
                f' level = {self.level!r}, service = {self.service!r}, message = {self.message!r}')