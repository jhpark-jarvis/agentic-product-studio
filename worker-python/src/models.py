from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


TASK_STATUSES = ["예정", "진행중", "검토중", "완료", "보류"]
TASK_PRIORITIES = ["낮음", "보통", "높음", "긴급"]
DOCUMENT_TYPES = ["기획서", "기술문서", "회의록", "참고자료", "API 문서", "기타"]
SCHEDULE_TYPES = ["개발", "회의", "테스트", "배포", "리뷰", "기타"]
WBS_PLATFORM_OPTIONS = ["Agentic Product Studio", "외부 에셋 카탈로그(게임 제작)"]


class MemberPayload(BaseModel):
    name: str = Field(min_length=1)
    role: str = ""
    part: str = ""
    contact: str = ""
    is_active: int = 1


class SchedulePayload(BaseModel):
    title: str = Field(min_length=1)
    description: str = ""
    start_date: str
    end_date: str
    assignee_id: int | None = None
    wbs_task_id: int | None = None
    schedule_type: str = SCHEDULE_TYPES[0]


class DocumentPayload(BaseModel):
    title: str = Field(min_length=1)
    doc_type: str = DOCUMENT_TYPES[-1]
    folder_id: int | None = None
    new_folder_name: str = ""
    content: str = ""
    author_id: int | None = None
    tags: str = ""
    is_hidden: int = 0
    related_task_ids: list[int] = []


class DocumentFolderPayload(BaseModel):
    doc_type: str
    folder_name: str = Field(min_length=1)


class WbsPayload(BaseModel):
    parent_id: int | None = None
    title: str = Field(min_length=1)
    description: str = ""
    assignee_id: int | None = None
    platform: str = WBS_PLATFORM_OPTIONS[0]
    status: str = TASK_STATUSES[0]
    priority: str = TASK_PRIORITIES[1]
    start_date: str | None = None
    due_date: str | None = None
    completed_date: str | None = None
    progress: int = 0
    notes: str = ""
    document_ids: list[int] = []
