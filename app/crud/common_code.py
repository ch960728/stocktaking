from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.common_code import CommonCode, CommonCodeGroup, CommonCodeGroupEnum

GROUP_SEED = {
    CommonCodeGroupEnum.UNIT: "단위",
    CommonCodeGroupEnum.LOCATION: "위치",
    CommonCodeGroupEnum.CATEGORY: "구분",
    CommonCodeGroupEnum.SIZE_ABBR: "규격약식",
}


# 2026-10-29: crud 함수별 기능/내용 설명 주석 추가
# 앱 기동 시 4개 고정 그룹(UNIT/LOCATION/CATEGORY/SIZE_ABBR)이 없으면 생성.
# 이미 있으면 건너뛰므로 매 기동마다 호출해도 안전함(idempotent).
def seed_groups(db: Session) -> None:
    """Ensure the four fixed code groups exist. Idempotent, safe to call on
    every app startup."""
    existing = {g.group_code for g in db.scalars(select(CommonCodeGroup))}
    for group_code, group_name in GROUP_SEED.items():
        if group_code.value not in existing:
            db.add(CommonCodeGroup(group_code=group_code.value, group_name=group_name))
    db.commit()


# 전체 공통코드 그룹 목록 조회 (4개 고정 그룹, id 순)
def get_groups(db: Session) -> list[CommonCodeGroup]:
    return list(db.scalars(select(CommonCodeGroup).order_by(CommonCodeGroup.id)))


# group_code(UNIT/LOCATION/CATEGORY/SIZE_ABBR 문자열)로 그룹 1건 조회
def get_group_by_code(db: Session, group_code: str) -> CommonCodeGroup | None:
    return db.scalar(select(CommonCodeGroup).where(CommonCodeGroup.group_code == group_code))


# 공통코드 목록 조회 — group_code/keyword(이름 부분일치)/is_active로 필터링
def get_codes(
    db: Session,
    group_code: str | None = None,
    keyword: str | None = None,
    is_active: bool | None = True,
) -> list[CommonCode]:
    query = select(CommonCode).options(joinedload(CommonCode.group))
    if group_code is not None:
        query = query.join(CommonCodeGroup).where(CommonCodeGroup.group_code == group_code)
    if keyword:
        query = query.where(CommonCode.name.ilike(f"%{keyword}%"))
    if is_active is not None:
        query = query.where(CommonCode.is_active == is_active)
    query = query.order_by(CommonCode.group_id, CommonCode.sort_order, CommonCode.id)
    return list(db.scalars(query).unique())


# 공통코드 1건 조회 (id 기준, 그룹 정보 포함)
def get_code(db: Session, code_id: int) -> CommonCode | None:
    return db.scalar(
        select(CommonCode).options(joinedload(CommonCode.group)).where(CommonCode.id == code_id)
    )


# 공통코드 등록 — 특정 그룹에 code/name/sort_order로 신규 행 생성
def create_code(db: Session, group_id: int, code: str, name: str, sort_order: int) -> CommonCode:
    row = CommonCode(group_id=group_id, code=code, name=name, sort_order=sort_order)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# 공통코드 부분 수정 (전달된 필드만 반영)
def update_code(db: Session, row: CommonCode, **fields) -> CommonCode:
    """`fields` should already be filtered to only the keys the client
    explicitly sent (e.g. via Pydantic's `exclude_unset`), so an explicit
    None is a real value to write, not a "no change" placeholder."""
    for key, value in fields.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row


# 공통코드 논리 삭제 (is_active=False, 물리 삭제 없음)
def deactivate_code(db: Session, row: CommonCode) -> CommonCode:
    row.is_active = False
    db.commit()
    db.refresh(row)
    return row


# 같은 그룹 내에 동일 code가 이미 있는지 확인 (등록/수정 시 중복 체크, exclude_id로 자기 자신 제외)
def code_exists_in_group(
    db: Session, group_id: int, code: str, exclude_id: int | None = None
) -> bool:
    query = select(CommonCode).where(CommonCode.group_id == group_id, CommonCode.code == code)
    if exclude_id is not None:
        query = query.where(CommonCode.id != exclude_id)
    return db.scalar(query) is not None
