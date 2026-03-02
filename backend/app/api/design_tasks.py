
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_community, get_current_user
from app.database import get_db
from app.models.design import DesignTask
from app.models.user import User
from app.schemas.design import (
    DesignTaskCreate,
    DesignTaskListItem,
    DesignTaskOut,
    DesignTaskStatusUpdate,
    DesignTaskUpdate,
)

router = APIRouter()


def _build_task_out(task: DesignTask) -> DesignTaskOut:
    assignee_name = None
    if task.assignee:
        assignee_name = task.assignee.full_name or task.assignee.username
    content_title = None
    if task.content:
        content_title = task.content.title
    return DesignTaskOut(
        id=task.id,
        title=task.title,
        description=task.description,
        task_type=task.task_type,
        status=task.status,
        priority=task.priority,
        assignee_id=task.assignee_id,
        assignee_name=assignee_name,
        due_date=task.due_date,
        community_id=task.community_id,
        created_by_user_id=task.created_by_user_id,
        content_id=task.content_id,
        content_title=content_title,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def _build_list_item(task: DesignTask) -> DesignTaskListItem:
    assignee_name = None
    if task.assignee:
        assignee_name = task.assignee.full_name or task.assignee.username
    content_title = None
    if task.content:
        content_title = task.content.title
    return DesignTaskListItem(
        id=task.id,
        title=task.title,
        task_type=task.task_type,
        status=task.status,
        priority=task.priority,
        assignee_id=task.assignee_id,
        assignee_name=assignee_name,
        due_date=task.due_date,
        content_id=task.content_id,
        content_title=content_title,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )




@router.get("/", response_model=dict)
async def list_design_tasks(
    status: str | None = Query(None),
    task_type: str | None = Query(None),
    priority: str | None = Query(None),
    assignee_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """列出社区的设计任务（支持过滤和分页）。"""
    query = db.query(DesignTask).filter(DesignTask.community_id == community_id)
    if status:
        query = query.filter(DesignTask.status == status)
    if task_type:
        query = query.filter(DesignTask.task_type == task_type)
    if priority:
        query = query.filter(DesignTask.priority == priority)
    if assignee_id is not None:
        query = query.filter(DesignTask.assignee_id == assignee_id)

    total = query.count()
    tasks = query.order_by(DesignTask.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [_build_list_item(t) for t in tasks],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/", response_model=DesignTaskOut, status_code=201)
async def create_design_task(
    data: DesignTaskCreate,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DesignTaskOut:
    """创建设计任务。"""
    task = DesignTask(
        title=data.title,
        description=data.description,
        task_type=data.task_type,
        priority=data.priority,
        assignee_id=data.assignee_id,
        due_date=data.due_date,
        content_id=data.content_id,
        community_id=community_id,
        created_by_user_id=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return _build_task_out(task)


@router.get("/{task_id}", response_model=DesignTaskOut)
async def get_design_task(
    task_id: int,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DesignTaskOut:
    """获取设计任务详情。"""
    task = db.query(DesignTask).filter(DesignTask.id == task_id, DesignTask.community_id == community_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="设计任务不存在")
    return _build_task_out(task)


def _check_permission(task: DesignTask, current_user: User, db: Session) -> None:
    """创建者、被分配人或超级用户可操作。"""
    if current_user.is_superuser:
        return
    if task.created_by_user_id == current_user.id:
        return
    if task.assignee_id == current_user.id:
        return
    # Community admin check
    from sqlalchemy import text

    row = db.execute(
        text("SELECT role FROM community_users WHERE user_id = :uid AND community_id = :cid"),
        {"uid": current_user.id, "cid": task.community_id},
    ).fetchone()
    if row and row[0] == "admin":
        return
    raise HTTPException(status_code=403, detail="没有权限操作此设计任务")


@router.put("/{task_id}", response_model=DesignTaskOut)
async def update_design_task(
    task_id: int,
    data: DesignTaskUpdate,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DesignTaskOut:
    """更新设计任务。"""
    task = db.query(DesignTask).filter(DesignTask.id == task_id, DesignTask.community_id == community_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="设计任务不存在")
    _check_permission(task, current_user, db)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return _build_task_out(task)


@router.patch("/{task_id}/status", response_model=DesignTaskOut)
async def update_design_task_status(
    task_id: int,
    data: DesignTaskStatusUpdate,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DesignTaskOut:
    """快速更新设计任务状态。"""
    valid_statuses = {"not_started", "in_progress", "review", "completed"}
    if data.status not in valid_statuses:
        raise HTTPException(status_code=422, detail=f"无效状态，可选值：{', '.join(valid_statuses)}")

    task = db.query(DesignTask).filter(DesignTask.id == task_id, DesignTask.community_id == community_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="设计任务不存在")
    _check_permission(task, current_user, db)

    task.status = data.status
    db.commit()
    db.refresh(task)
    return _build_task_out(task)


@router.delete("/{task_id}", status_code=204)
async def delete_design_task(
    task_id: int,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """删除设计任务。"""
    task = db.query(DesignTask).filter(DesignTask.id == task_id, DesignTask.community_id == community_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="设计任务不存在")
    _check_permission(task, current_user, db)

    db.delete(task)
    db.commit()
