from datetime import date, datetime

from pydantic import BaseModel

# ─── Design Task ─────────────────────────────────────────────────────────────


class DesignTaskCreate(BaseModel):
    title: str
    description: str | None = None
    task_type: str = "other"
    priority: str = "medium"
    assignee_id: int | None = None
    due_date: date | None = None
    content_id: int | None = None


class DesignTaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    task_type: str | None = None
    status: str | None = None
    priority: str | None = None
    assignee_id: int | None = None
    due_date: date | None = None
    content_id: int | None = None


class DesignTaskStatusUpdate(BaseModel):
    status: str


class DesignTaskOut(BaseModel):
    id: int
    title: str
    description: str | None
    task_type: str
    status: str
    priority: str
    assignee_id: int | None
    assignee_name: str | None  # 经办人姓名（冗余字段，方便前端展示）
    due_date: date | None
    community_id: int
    created_by_user_id: int | None
    content_id: int | None
    content_title: str | None  # 关联内容标题（冗余字段）
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DesignTaskListItem(BaseModel):
    id: int
    title: str
    task_type: str
    status: str
    priority: str
    assignee_id: int | None
    assignee_name: str | None
    due_date: date | None
    content_id: int | None
    content_title: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Asset ───────────────────────────────────────────────────────────────────


class AssetUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    asset_type: str | None = None
    tags: list[str] | None = None


class AssetOut(BaseModel):
    id: int
    name: str
    description: str | None
    asset_type: str
    file_url: str
    file_size: int | None
    mime_type: str | None
    tags: list[str]
    community_id: int
    uploaded_by_user_id: int | None
    uploader_name: str | None  # 上传者姓名
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
