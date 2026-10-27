from pydantic import BaseModel, ConfigDict, Field


class CommonCodeGroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    group_code: str = Field(description="그룹 코드 (고정값: UNIT/LOCATION/CATEGORY/SIZE_ABBR)")
    group_name: str = Field(description="그룹 화면 표시명 (예: 단위, 위치, 구분, 규격약식)")


class CommonCodeBrief(BaseModel):
    """다른 리소스(품목 등)에 중첩되어 보일 때 쓰는 축약형."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str


class CommonCodeCreate(BaseModel):
    group_code: str = Field(description="등록할 그룹의 코드 (UNIT/LOCATION/CATEGORY/SIZE_ABBR 중 하나)")
    code: str = Field(description="코드값 (그룹 내에서 유일해야 함)")
    name: str = Field(description="화면 표시명")
    sort_order: int = Field(default=0, description="목록/드롭다운 정렬 순서 (작을수록 앞)")


class CommonCodeUpdate(BaseModel):
    """그룹(group_code/group_id) 자체는 수정 대상이 아니다 — 코드가 속한
    그룹을 바꾸는 것은 일반적인 사용 사례가 아니라 의도적으로 지원하지 않음."""

    code: str | None = Field(default=None, description="보낸 필드만 수정된다(부분 수정)")
    name: str | None = None
    sort_order: int | None = None
    is_active: bool | None = Field(default=None, description="false로 바꾸면 논리 삭제와 동일")


class CommonCodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    group_code: str
    group_name: str
    code: str
    name: str
    sort_order: int
    is_active: bool
