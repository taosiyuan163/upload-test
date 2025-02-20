from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class UploadTaskRequest(BaseModel):
    platform: Literal['douyin', 'tencent', 'tiktok', 'bilibili', 'kuaishou'] = Field(..., description="上传平台")
    account_name: str = Field(..., description="平台的账号名")
    action: Literal['login', 'upload'] = Field(..., description="登录/上传视频")
    video_path: Optional[str] = Field(None, description="action=upload时需要，视频路径")
    # options: Optional[List[str]] = Field(None, description="如果默认['-pt', 0]立即发布")
