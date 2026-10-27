from datetime import date

from sqlalchemy import DECIMAL, Date, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import AuditMixin


class StocktakeRecord(Base, AuditMixin):
    __tablename__ = "stocktake_records"
    __table_args__ = (
        Index("ix_stocktake_item", "item_id"),
        Index("ix_stocktake_date", "survey_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(DECIMAL(12, 2), nullable=False)
    survey_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    item = relationship("Item")
