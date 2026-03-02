import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_community, get_current_user
from app.database import get_db
from app.models.design import Asset
from app.models.user import User
from app.schemas.design import AssetOut, AssetUpdate
from app.services.storage import StorageService, get_storage

router = APIRouter()

ALLOWED_ASSET_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp",  # images
    ".svg",                                      # vector
    ".pdf", ".ai", ".psd", ".fig", ".zip",       # brand files / templates
}
MAX_ASSET_SIZE = 50 * 1024 * 1024  # 50 MB


def _build_asset_out(asset: Asset) -> AssetOut:
    uploader_name = None
    if asset.uploader:
        uploader_name = asset.uploader.full_name or asset.uploader.username
    return AssetOut(
        id=asset.id,
        name=asset.name,
        description=asset.description,
        asset_type=asset.asset_type,
        file_url=asset.file_url,
        file_size=asset.file_size,
        mime_type=asset.mime_type,
        tags=asset.tags or [],
        community_id=asset.community_id,
        uploaded_by_user_id=asset.uploaded_by_user_id,
        uploader_name=uploader_name,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


def _check_asset_permission(asset: Asset, current_user: User, db: Session) -> None:
    """上传者或社区管理员/超级用户可操作。"""
    if current_user.is_superuser:
        return
    if asset.uploaded_by_user_id == current_user.id:
        return
    from sqlalchemy import text

    row = db.execute(
        text("SELECT role FROM community_users WHERE user_id = :uid AND community_id = :cid"),
        {"uid": current_user.id, "cid": asset.community_id},
    ).fetchone()
    if row and row[0] == "admin":
        return
    raise HTTPException(status_code=403, detail="没有权限操作此素材")


@router.get("/", response_model=dict)
async def list_assets(
    asset_type: str | None = Query(None),
    keyword: str | None = Query(None),
    tags: str | None = Query(None, description="逗号分隔的标签列表"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """列出社区素材库（支持过滤和分页）。"""
    query = db.query(Asset).filter(Asset.community_id == community_id)
    if asset_type:
        query = query.filter(Asset.asset_type == asset_type)
    if keyword:
        query = query.filter(Asset.name.ilike(f"%{keyword}%"))

    total = query.count()
    assets = query.order_by(Asset.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    # Filter by tags in Python (JSON column filtering is DB-specific)
    items = [_build_asset_out(a) for a in assets]
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        items = [a for a in items if any(tag in a.tags for tag in tag_list)]
        total = len(items)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/upload", response_model=AssetOut, status_code=201)
async def upload_asset(
    file: UploadFile = File(...),
    name: str = Form(...),
    asset_type: str = Form(...),
    description: str | None = Form(None),
    tags: str | None = Form(None, description="逗号分隔的标签"),
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssetOut:
    """上传素材文件并创建素材记录。"""
    valid_types = {"image", "icon", "brand_file", "template"}
    if asset_type not in valid_types:
        raise HTTPException(status_code=422, detail=f"无效素材类型，可选值：{', '.join(valid_types)}")

    if not file.filename:
        raise HTTPException(status_code=400, detail="未提供文件名")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_ASSET_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式：{ext}。支持：{', '.join(sorted(ALLOWED_ASSET_EXTENSIONS))}",
        )

    file_content = await file.read()
    if len(file_content) > MAX_ASSET_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过 50MB")

    storage = get_storage()
    key = StorageService.generate_key(ext, "assets")
    file_url = storage.save(file_content, key)

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    asset = Asset(
        name=name,
        description=description,
        asset_type=asset_type,
        file_url=file_url,
        file_key=key,
        file_size=len(file_content),
        mime_type=file.content_type,
        tags=tag_list,
        community_id=community_id,
        uploaded_by_user_id=current_user.id,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return _build_asset_out(asset)


@router.get("/{asset_id}", response_model=AssetOut)
async def get_asset(
    asset_id: int,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssetOut:
    """获取素材详情。"""
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.community_id == community_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="素材不存在")
    return _build_asset_out(asset)


@router.put("/{asset_id}", response_model=AssetOut)
async def update_asset(
    asset_id: int,
    data: AssetUpdate,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AssetOut:
    """更新素材元数据（名称、描述、标签等）。"""
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.community_id == community_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="素材不存在")
    _check_asset_permission(asset, current_user, db)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)
    db.commit()
    db.refresh(asset)
    return _build_asset_out(asset)


@router.delete("/{asset_id}", status_code=204)
async def delete_asset(
    asset_id: int,
    community_id: int = Depends(get_current_community),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """删除素材（同时从存储中删除文件）。"""
    asset = db.query(Asset).filter(Asset.id == asset_id, Asset.community_id == community_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="素材不存在")
    _check_asset_permission(asset, current_user, db)

    # Delete from storage
    try:
        storage = get_storage()
        storage.delete(asset.file_key)
    except Exception:
        pass  # Storage deletion failure should not block DB record deletion

    db.delete(asset)
    db.commit()
