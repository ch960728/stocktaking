from sqlalchemy import DECIMAL, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import AuditMixin


class Item(Base, AuditMixin):
    __tablename__ = "items"
    __table_args__ = (
        Index("ix_items_item_name", "item_name"),
        Index("ix_items_item_no", "item_no"),
        Index("ix_items_barcode", "barcode"),
        Index("ix_items_category", "category_id"),
        Index("ix_items_location", "location_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    item_no: Mapped[str | None] = mapped_column(String(100), nullable=True)
    barcode: Mapped[str | None] = mapped_column(String(100), nullable=True)
    barcode_prefix: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("common_codes.id"), nullable=False)
    unit_id: Mapped[int] = mapped_column(ForeignKey("common_codes.id"), nullable=False)
    location_id: Mapped[int | None] = mapped_column(ForeignKey("common_codes.id"), nullable=True)
    size_abbr_id: Mapped[int | None] = mapped_column(ForeignKey("common_codes.id"), nullable=True)
    size_width: Mapped[float | None] = mapped_column(DECIMAL(10, 2), nullable=True)
    size_length: Mapped[float | None] = mapped_column(DECIMAL(10, 2), nullable=True)
    size_height: Mapped[float | None] = mapped_column(DECIMAL(10, 2), nullable=True)

    category = relationship("CommonCode", foreign_keys=[category_id])
    unit = relationship("CommonCode", foreign_keys=[unit_id])
    location = relationship("CommonCode", foreign_keys=[location_id])
    size_abbr = relationship("CommonCode", foreign_keys=[size_abbr_id])
