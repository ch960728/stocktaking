from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.crud.item import _EAGER as ITEM_EAGER
from app.crud.item import search_clause
from app.models.item import Item
from app.models.sensor_barcode import SensorBarcode
from app.models.stocktake import StocktakeRecord


def get_stocktakes(
    db: Session,
    search: str | None = None,
    category_id: int | None = None,
    location_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    is_active: bool | None = True,
    limit: int = 50,
    offset: int = 0,
) -> list[StocktakeRecord]:
    query = (
        select(StocktakeRecord)
        .join(StocktakeRecord.item)
        .options(joinedload(StocktakeRecord.item).options(*ITEM_EAGER))
    )
    if search:
        query = query.where(search_clause(search))
    if category_id is not None:
        query = query.where(Item.category_id == category_id)
    if location_id is not None:
        query = query.where(Item.location_id == location_id)
    if date_from is not None:
        query = query.where(StocktakeRecord.survey_date >= date_from)
    if date_to is not None:
        query = query.where(StocktakeRecord.survey_date <= date_to)
    if is_active is not None:
        query = query.where(StocktakeRecord.is_active == is_active)
    query = (
        query.order_by(StocktakeRecord.survey_date.desc(), StocktakeRecord.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.scalars(query).unique())


def get_latest_quantity(db: Session, item_id: int) -> float | None:
    row = db.scalar(
        select(StocktakeRecord)
        .where(StocktakeRecord.item_id == item_id, StocktakeRecord.is_active == True)  # noqa: E712
        .order_by(StocktakeRecord.survey_date.desc(), StocktakeRecord.id.desc())
        .limit(1)
    )
    return float(row.quantity) if row else None


def get_stocktake(db: Session, record_id: int) -> StocktakeRecord | None:
    return db.scalar(
        select(StocktakeRecord)
        .options(joinedload(StocktakeRecord.item).options(*ITEM_EAGER))
        .where(StocktakeRecord.id == record_id)
    )


def create_stocktake(db: Session, **fields) -> StocktakeRecord:
    row = StocktakeRecord(**fields)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_stocktake(db: Session, row: StocktakeRecord, **fields) -> StocktakeRecord:
    """`fields` should already be filtered to only the keys the client
    explicitly sent (e.g. via Pydantic's `exclude_unset`), so an explicit
    None is a real value to write, not a "no change" placeholder."""
    for key, value in fields.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


def deactivate_stocktake(db: Session, row: StocktakeRecord) -> StocktakeRecord:
    row.is_active = False
    db.commit()
    db.refresh(row)
    return row


def get_status(
    db: Session,
    search: str | None = None,
    category_id: int | None = None,
    location_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[tuple[Item, float | None, date | None, int, float | None]]:
    """Latest active stocktake record per item, left-joined onto all active
    items so items never counted still appear (with null quantity/date).
    Also left-joins the count of each item's registered sensor barcodes
    (0 for items that don't use barcode-based tracking).

    `current_stock` is the one number meant to answer "how many do we
    actually have": barcode-tracked units (sensor_barcodes) PLUS whatever
    was manually recorded on top for units with no barcode (last_quantity
    -- for non-barcode items this manual number *is* the whole stock, same
    as before). It's None only when neither exists (never counted, no
    barcodes) so the UI can still show "-" for untouched items."""
    ranked = (
        select(
            StocktakeRecord.item_id.label("item_id"),
            StocktakeRecord.quantity.label("quantity"),
            StocktakeRecord.survey_date.label("survey_date"),
            func.row_number()
            .over(
                partition_by=StocktakeRecord.item_id,
                order_by=(StocktakeRecord.survey_date.desc(), StocktakeRecord.id.desc()),
            )
            .label("rn"),
        )
        .where(StocktakeRecord.is_active == True)  # noqa: E712
        .subquery()
    )
    latest = select(ranked).where(ranked.c.rn == 1).subquery()

    barcode_counts = (
        select(
            SensorBarcode.item_id.label("item_id"),
            func.count(SensorBarcode.id).label("cnt"),
        )
        .where(SensorBarcode.is_active == True)  # noqa: E712
        .group_by(SensorBarcode.item_id)
        .subquery()
    )

    query = (
        select(Item, latest.c.quantity, latest.c.survey_date, barcode_counts.c.cnt)
        .options(*ITEM_EAGER)
        .outerjoin(latest, latest.c.item_id == Item.id)
        .outerjoin(barcode_counts, barcode_counts.c.item_id == Item.id)
        .where(Item.is_active == True)  # noqa: E712
    )
    if search:
        query = query.where(search_clause(search))
    if category_id is not None:
        query = query.where(Item.category_id == category_id)
    if location_id is not None:
        query = query.where(Item.location_id == location_id)
    query = query.order_by(Item.item_name).limit(limit).offset(offset)

    results = []
    for item, quantity, survey_date, barcode_count in db.execute(query).unique():
        barcode_count = barcode_count or 0
        current_stock = None if quantity is None and barcode_count == 0 else (quantity or 0) + barcode_count
        results.append((item, quantity, survey_date, barcode_count, current_stock))
    return results
