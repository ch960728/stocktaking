from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import AuditMixin


class SensorBarcode(Base, AuditMixin):
    """One row per physical sensor unit's own unique barcode. Which item
    (product line) it belongs to is resolved at scan time by matching the
    item's `barcode_prefix` (e.g. si/so/sj) as a prefix of this value --
    see `crud/item.py::find_item_by_scanned_barcode`."""

    __tablename__ = "sensor_barcodes"
    __table_args__ = (Index("ix_sensor_barcodes_item", "item_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), nullable=False)
    barcode: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)

    item = relationship("Item")
