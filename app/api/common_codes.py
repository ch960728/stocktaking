from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import common_code as crud
from app.core.database import get_db
from app.models.common_code import CommonCodeGroupEnum
from app.schemas.common_code import (
    CommonCodeCreate,
    CommonCodeGroupOut,
    CommonCodeOut,
    CommonCodeUpdate,
)

router = APIRouter(prefix="/api/common-codes", tags=["common-codes"])


def _serialize(row) -> CommonCodeOut:
    return CommonCodeOut(
        id=row.id,
        group_code=row.group.group_code,
        group_name=row.group.group_name,
        code=row.code,
        name=row.name,
        sort_order=row.sort_order,
        is_active=row.is_active,
    )


@router.get(
    "/groups",
    response_model=list[CommonCodeGroupOut],
    summary="공통코드 그룹 목록 조회",
    description="UNIT/LOCATION/CATEGORY/SIZE_ABBR 4개 고정 그룹을 반환한다. 앱 시작 시 자동 시드되며 이 API로 그룹을 추가/삭제할 수는 없다.",
)
def list_groups(db: Session = Depends(get_db)):
    return crud.get_groups(db)


@router.get(
    "",
    response_model=list[CommonCodeOut],
    summary="공통코드 목록 조회",
    description="`group_code`로 특정 그룹(예: LOCATION)의 코드값만 좁혀서 조회할 수 있다. 품목 등록 폼의 구분/단위/위치/규격약식 드롭다운이 이 엔드포인트로 채워진다.",
)
def list_codes(
    group_code: str | None = None,
    keyword: str | None = None,
    is_active: bool | None = True,
    db: Session = Depends(get_db),
):
    rows = crud.get_codes(db, group_code=group_code, keyword=keyword, is_active=is_active)
    return [_serialize(r) for r in rows]


@router.post(
    "",
    response_model=CommonCodeOut,
    status_code=201,
    summary="공통코드 등록",
    description="group_code가 가리키는 그룹 안에 새 코드값을 추가한다 (예: LOCATION 그룹에 '3층 창고' 추가).",
    responses={
        400: {"description": "group_code가 UNIT/LOCATION/CATEGORY/SIZE_ABBR 중 하나가 아니거나 해당 그룹이 없음"},
        409: {"description": "같은 그룹 안에 동일한 code가 이미 존재함"},
    },
)
def create_code(payload: CommonCodeCreate, db: Session = Depends(get_db)):
    if payload.group_code not in {g.value for g in CommonCodeGroupEnum}:
        raise HTTPException(400, f"알 수 없는 공통코드 그룹입니다: {payload.group_code}")
    group = crud.get_group_by_code(db, payload.group_code)
    if group is None:
        raise HTTPException(400, f"공통코드 그룹을 찾을 수 없습니다: {payload.group_code}")
    if crud.code_exists_in_group(db, group.id, payload.code):
        raise HTTPException(409, f"이미 등록된 코드입니다: {payload.code}")
    row = crud.create_code(db, group.id, payload.code, payload.name, payload.sort_order)
    return _serialize(row)


@router.put(
    "/{code_id}",
    response_model=CommonCodeOut,
    summary="공통코드 수정",
    description="code/name/sort_order/is_active만 수정 가능 — 소속 그룹(group_code)은 이 API로 바꿀 수 없다.",
    responses={
        404: {"description": "해당 id의 공통코드가 없음"},
        409: {"description": "같은 그룹 안에 동일한 code가 이미 존재함"},
    },
)
def update_code(code_id: int, payload: CommonCodeUpdate, db: Session = Depends(get_db)):
    row = crud.get_code(db, code_id)
    if row is None:
        raise HTTPException(404, "공통코드를 찾을 수 없습니다")
    if payload.code and crud.code_exists_in_group(db, row.group_id, payload.code, exclude_id=row.id):
        raise HTTPException(409, f"이미 등록된 코드입니다: {payload.code}")
    row = crud.update_code(db, row, **payload.model_dump(exclude_unset=True))
    return _serialize(row)


@router.delete(
    "/{code_id}",
    status_code=204,
    summary="공통코드 삭제 (논리 삭제)",
    description="실제로 행을 지우지 않고 is_active를 false로 바꾼다. 이 코드를 참조 중인 품목이 있어도 막지 않으므로 주의해서 사용할 것.",
    responses={404: {"description": "해당 id의 공통코드가 없음"}},
)
def delete_code(code_id: int, db: Session = Depends(get_db)):
    row = crud.get_code(db, code_id)
    if row is None:
        raise HTTPException(404, "공통코드를 찾을 수 없습니다")
    crud.deactivate_code(db, row)
