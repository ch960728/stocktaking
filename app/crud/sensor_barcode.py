from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.crud.item import _EAGER as ITEM_EAGER
from app.models.sensor_barcode import SensorBarcode

_EAGER = (joinedload(SensorBarcode.item).options(*ITEM_EAGER),)


# 2026-10-29: crud 함수별 기능/내용 설명 주석 추가
# 센서 바코드 목록 조회 — item_id/is_active로 필터링, 최신 등록순
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


# 센서 바코드 1건 조회 (id 기준)
def get_barcode(db: Session, barcode_id: int) -> SensorBarcode | None:
    return db.scalar(select(SensorBarcode).options(*_EAGER).where(SensorBarcode.id == barcode_id))


# 바코드 문자열(barcode, UNIQUE)로 1건 조회 — 스캔 시 기존 등록/제거 여부 판단에 사용
def get_barcode_by_value(db: Session, barcode: str) -> SensorBarcode | None:
    return db.scalar(select(SensorBarcode).options(*_EAGER).where(SensorBarcode.barcode == barcode))


# 센서 바코드 신규 등록 (입고 스캔)
def create_barcode(db: Session, item_id: int, barcode: str) -> SensorBarcode:
    row = SensorBarcode(item_id=item_id, barcode=barcode)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# 센서 바코드 논리 삭제 (출고 스캔, 또는 현황 페이지에서 개별 제거)
def deactivate_barcode(db: Session, row: SensorBarcode) -> SensorBarcode:
    row.is_active = False
    db.commit()
    db.refresh(row)
    return row


# 제거됐던(비활성) 바코드를 다시 입고 — barcode UNIQUE 제약 때문에 새 행을 만들지 않고 기존 행을 재활성화
def reactivate_barcode(db: Session, row: SensorBarcode) -> SensorBarcode:
    """A unit that was scanned out (removed) can come back into stock later
    under the same physical barcode -- `barcode` is globally UNIQUE, so we
    must reuse that row rather than trying to insert a second one."""
    row.is_active = True
    db.commit()
    db.refresh(row)
    return row
