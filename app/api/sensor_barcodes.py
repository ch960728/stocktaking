from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import item as item_crud
from app.crud import sensor_barcode as crud
from app.core.database import get_db
from app.schemas.sensor_barcode import SensorBarcodeOut, SensorBarcodeScanRequest

router = APIRouter(prefix="/api/sensor-barcodes", tags=["sensor-barcodes"])


@router.get(
    "",
    response_model=list[SensorBarcodeOut],
    summary="센서 바코드 목록 조회",
    description="`item_id`로 특정 품목의 등록된 바코드 전체를 조회한다. 현황 페이지의 'N건 보기'를 눌렀을 때 호출된다.",
)
def list_barcodes(
    item_id: int | None = None,
    is_active: bool | None = True,
    db: Session = Depends(get_db),
):
    """Backs the 현황 page's per-item barcode list/count."""
    return crud.get_barcodes(db, item_id=item_id, is_active=is_active)


@router.post(
    "/scan",
    response_model=SensorBarcodeOut,
    status_code=201,
    summary="바코드 스캔 - 입고(등록)",
    description=(
        "스캔한 값을 품목들의 barcode_prefix와 접두어 매칭해 어느 품목인지 "
        "찾고(가장 긴 접두어 우선), 그 바코드를 개별 레코드로 저장한다. "
        "수량을 +1 하는 게 아니라 '이 개체가 존재한다'는 사실 자체를 기록하는 "
        "것이며, stocktake_records는 전혀 건드리지 않는다."
    ),
    responses={
        404: {"description": "스캔값과 일치하는 barcode_prefix를 가진 품목이 없음"},
        409: {"description": "이미 활성 상태로 등록된 바코드 (중복 스캔)"},
    },
)
def scan_barcode(payload: SensorBarcodeScanRequest, db: Session = Depends(get_db)):
    """입고(등록): each scan is one physical unit's own unique barcode, not
    a quantity delta -- it's stored as its own row (see SensorBarcode), not
    folded into stocktake_records."""
    value = payload.barcode.strip()
    existing = crud.get_barcode_by_value(db, value)
    if existing is not None:
        if existing.is_active:
            raise HTTPException(409, f"이미 등록된 바코드입니다: {value}")
        # this unit was previously scanned out (removed) and is back in
        # stock -- `barcode` is globally unique, so reuse the row.
        return crud.reactivate_barcode(db, existing)
    item = item_crud.find_item_by_scanned_barcode(db, value)
    if item is None:
        raise HTTPException(404, f"등록되지 않은 바코드 구분입니다: {value}")
    return crud.create_barcode(db, item_id=item.id, barcode=value)


@router.post(
    "/remove",
    response_model=SensorBarcodeOut,
    summary="바코드 스캔 - 출고(제거)",
    description=(
        "스캔한 값과 정확히 일치하는 활성 바코드 1건을 찾아 논리 삭제한다. "
        "수량을 뭉뚱그려 줄이는 대신, 어느 개체가 빠졌는지 항상 명확하게 "
        "남기기 위한 경로다."
    ),
    responses={404: {"description": "등록된 적이 없거나 이미 제거된 바코드"}},
)
def remove_barcode(payload: SensorBarcodeScanRequest, db: Session = Depends(get_db)):
    """출고(제거): scanning the specific unit that is leaving stock, so the
    system knows exactly which sensor is gone -- rather than guessing from
    an aggregate quantity decrease on the 재고 등록 page."""
    value = payload.barcode.strip()
    row = crud.get_barcode_by_value(db, value)
    if row is None or not row.is_active:
        raise HTTPException(404, f"등록되지 않았거나 이미 제거된 바코드입니다: {value}")
    return crud.deactivate_barcode(db, row)


@router.delete(
    "/{barcode_id}",
    status_code=204,
    summary="바코드 삭제 (id 기준, 논리 삭제)",
    description="현황 페이지의 펼친 바코드 목록에서 개별 '제거' 버튼이 호출하는 경로 — 실물 바코드를 다시 스캔하기 어려운 상황에서 id로 직접 제거한다.",
    responses={404: {"description": "해당 id의 바코드가 없음"}},
)
def delete_barcode(barcode_id: int, db: Session = Depends(get_db)):
    """Direct removal from the 현황 page's expanded list, by id, for when
    the user is correcting the list without rescanning the physical unit."""
    row = crud.get_barcode(db, barcode_id)
    if row is None:
        raise HTTPException(404, "바코드를 찾을 수 없습니다")
    crud.deactivate_barcode(db, row)
