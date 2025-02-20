from fastapi import APIRouter

from my.schemas.social_media_schema import UploadTaskRequest
from my.services.social_media_ser import social_media_service

social_router = APIRouter(prefix="/social")


@social_router.post("/upload")
async def submit_task(task: UploadTaskRequest):
    # 将任务添加到队列中
    await social_media_service.upload(task)
    return {"message": "任务提交成功."}