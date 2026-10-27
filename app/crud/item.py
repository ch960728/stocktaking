from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.item import Item

_EAGER = (
    joinedload(Item.category),
    joinedload(Item.unit),
    joinedload(Item.location),
    joinedload(Item.size_abbr),
)


def search_clause(search: str):
    """Shared text-search condition (품목명/품번/바코드/바코드구분) for items
    and for anything joined to items (stocktakes, status)."""
    pattern = f"%{search}%"
    return or_(
        Item.item_name.ilike(pattern),
        Item.item_no.ilike(pattern),
        Item.barcode.ilike(pattern),
        Item.barcode_prefix.ilike(pattern),
    )


def _item_filter_conditions(
    search: str | None, category_id: int | None, location_id: int | None, is_active: bool | None
):
    """Shared by get_items/count_items so the two can never drift apart."""
    conditions = []
    if search:
        conditions.append(search_clause(search))
    if category_id is not None:
        conditions.append(Item.category_id == category_id)
    if location_id is not None:
        conditions.append(Item.location_id == location_id)
    if is_active is not None:
        conditions.append(Item.is_active == is_active)
    return conditions


def get_items(
    db: Session,
    search: str | None = None,
    category_id: int | None = None,
    location_id: int | None = None,
    is_active: bool | None = True,
    limit: int = 50,
    offset: int = 0,
) -> list[Item]:
    query = select(Item).options(*_EAGER)
    for condition in _item_filter_conditions(search, category_id, location_id, is_active):
        query = query.where(condition)
    query = query.order_by(Item.item_name).limit(limit).offset(offset)
    return list(db.scalars(query).unique())


def count_items(
    db: Session,
    search: str | None = None,
    category_id: int | None = None,
    location_id: int | None = None,
    is_active: bool | None = True,
) -> int:
    query = select(func.count(Item.id))
    for condition in _item_filter_conditions(search, category_id, location_id, is_active):
        query = query.where(condition)
    return db.scalar(query) or 0


def get_item(db: Session, item_id: int) -> Item | None:
    return db.scalar(select(Item).options(*_EAGER).where(Item.id == item_id))


def find_item_by_scanned_barcode(db: Session, scanned_value: str) -> Item | None:
    """Resolves a scanned sensor barcode to its item by PREFIX match:
    `barcode_prefix` (si/so/sj) identifies a product line, while the full
    scanned value is unique per physical unit (see SensorBarcode). Longest
    matching prefix wins in case two prefixes could both match (e.g. "s"
    and "si")."""
    candidates = db.scalars(
        select(Item)
        .options(*_EAGER)
        .where(Item.barcode_prefix.is_not(None), Item.is_active == True)  # noqa: E712
    ).unique()
    matches = [item for item in candidates if scanned_value.startswith(item.barcode_prefix)]
    if not matches:
        return None
    return max(matches, key=lambda item: len(item.barcode_prefix))


def barcode_prefix_exists(db: Session, barcode_prefix: str, exclude_id: int | None = None) -> bool:
    """Checked before create/update so a duplicate 바코드구분 value is a
    clean 409 rather than a raw DB IntegrityError (the column also has a
    DB-level UNIQUE constraint as a backstop). Only active items count —
    a deactivated item's old prefix is freed for reuse (deactivate_item
    clears it on soft-delete for the same reason)."""
    query = select(Item).where(Item.barcode_prefix == barcode_prefix, Item.is_active.is_(True))
    if exclude_id is not None:
        query = query.where(Item.id != exclude_id)
    return db.scalar(query) is not None


def create_item(db: Session, **fields) -> Item:
    row = Item(**fields)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_item(db: Session, row: Item, **fields) -> Item:
    """`fields` should already be filtered to only the keys the client
    explicitly sent (e.g. via Pydantic's `exclude_unset`), so an explicit
    None is a real value to write, not a "no change" placeholder."""
    for key, value in fields.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


def deactivate_item(db: Session, row: Item) -> Item:
    row.is_active = False
    row.barcode_prefix = None
    db.commit()
    db.refresh(row)
    return row
