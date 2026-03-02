from sqlalchemy import JSON, Column, Date, DateTime, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship

from app.core.timezone import utc_now
from app.database import Base

# Association table for content → asset (many-to-many)
content_assets = Table(
    "content_assets",
    Base.metadata,
    Column("content_id", Integer, ForeignKey("contents.id", ondelete="CASCADE"), primary_key=True),
    Column("asset_id", Integer, ForeignKey("assets.id", ondelete="CASCADE"), primary_key=True),
)


class DesignTask(Base):
    """设计任务：独立的设计工作项，可选关联内容文章。"""

    __tablename__ = "design_tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    # poster / icon / illustration / logo / template / brand_guide / other
    task_type = Column(String(50), default="other", index=True)
    # not_started / in_progress / review / completed
    status = Column(String(50), default="not_started", index=True)
    # low / medium / high
    priority = Column(String(20), default="medium", index=True)

    assignee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    due_date = Column(Date, nullable=True)

    community_id = Column(Integer, ForeignKey("communities.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    # Optional link to a content article
    content_id = Column(Integer, ForeignKey("contents.id", ondelete="SET NULL"), nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    assignee = relationship("User", foreign_keys=[assignee_id])
    creator = relationship("User", foreign_keys=[created_by_user_id])
    content = relationship("Content", foreign_keys=[content_id])


class Asset(Base):
    """素材库：存储设计产出物（图片、图标、品牌文件、模板等）。"""

    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    # image / icon / brand_file / template
    asset_type = Column(String(50), nullable=False, index=True)
    file_url = Column(String(1000), nullable=False)
    file_key = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)  # bytes
    mime_type = Column(String(100), nullable=True)
    tags = Column(JSON, default=list)

    community_id = Column(Integer, ForeignKey("communities.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)

    uploader = relationship("User", foreign_keys=[uploaded_by_user_id])
    contents = relationship("Content", secondary="content_assets", back_populates="assets")
