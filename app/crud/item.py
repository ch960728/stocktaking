from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.item import Item

_EAGER = (
    joinedload(Item.category),
    joinedload(Item.unit),
    joinedload(Item.location),
    joinedload(Item.size_abbr),
)


# 2026-10-29: crud 함수별 기능/내용 설명 주석 추가
# 텍스트 검색 조건 — item_name/item_no/barcode/barcode_prefix 중 하나라도 부분일치하면 매칭.
# 품목 목록뿐 아니라 재고조사/현황 쿼리에서도 그대로 재사용됨(검색 조건이 어긋나지 않도록).
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


# 품목 목록 조회 — search/category_id/location_id/is_active로 필터링, 품목명순 페이지네이션
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


# get_items와 동일한 필터로 건수만 집계 (품목 목록 페이지의 "전체/조회결과 N개" 배지용)
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


# 품목 1건 조회 (id 기준, 구분/단위/위치/규격약식 eager load)
def get_item(db: Session, item_id: int) -> Item | None:
    return db.scalar(select(Item).options(*_EAGER).where(Item.id == item_id))


# 센서 바코드 스캔값으로 품목 찾기 — barcode_prefix 접두어 매칭 (정확매칭 아님)
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


# barcode_prefix(바코드구분) 중복 여부 확인 — 등록/수정 전 사전 체크로 409 응답용
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


# 품목 등록 — 전달된 필드로 신규 행 생성
def create_item(db: Session, **fields) -> Item:
    row = Item(**fields)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# 품목 부분 수정 (전달된 필드만 반영)
def update_item(db: Session, row: Item, **fields) -> Item:
    """`fields` should already be filtered to only the keys the client
    explicitly sent (e.g. via Pydantic's `exclude_unset`), so an explicit
    None is a real value to write, not a "no change" placeholder."""
    for key, value in fields.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


# 품목 논리 삭제 — is_active=False 전환 및 barcode_prefix 해제(다른 품목이 재사용할 수 있도록)
def deactivate_item(db: Session, row: Item) -> Item:
    row.is_active = False
    row.barcode_prefix = None
    db.commit()
    db.refresh(row)
    return row
