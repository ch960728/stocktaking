from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.crud.item import _EAGER as ITEM_EAGER
from app.models.sensor_barcode import SensorBarcode

_EAGER = (joinedload(SensorBarcode.item).options(*ITEM_EAGER),)


def get_barcodes(
    db: Session, item_id: int | None = None, is_active: bool | None = True
) -> list[SensorBarcode]:
    query = select(SensorBarcode).options(*_EAGER)
    if item_id is not None:
        query = query.where(SensorBarcode.item_id == item_id)
    if is_active is not None:
        query = query.where(SensorBarcode.is_active == is_active)
    query = query.order_by(SensorBarcode.created_at.desc())
    return list(db.scalars(query).unique())


def get_barcode(db: Session, barcode_id: int) -> SensorBarcode | None:
    return db.scalar(select(SensorBarcode).options(*_EAGER).where(SensorBarcode.id == barcode_id))


def get_barcode_by_value(db: Session, barcode: str) -> SensorBarcode | None:
    return db.scalar(select(SensorBarcode).options(*_EAGER).where(SensorBarcode.barcode == barcode))


def create_barcode(db: Session, item_id: int, barcode: str) -> SensorBarcode:
    row = SensorBarcode(item_id=item_id, barcode=barcode)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def deactivate_barcode(db: Session, row: SensorBarcode) -> SensorBarcode:
    row.is_active = False
    db.commit()
    db.refresh(row)
    return row


def reactivate_barcode(db: Session, row: SensorBarcode) -> SensorBarcode:
    """A unit that was scanned out (removed) can come back into stock later
    under the same physical barcode -- `barcode` is globally UNIQUE, so we
    must reuse that row rather than trying to insert a second one."""
    row.is_active = True
    db.commit()
    db.refresh(row)
    return row
