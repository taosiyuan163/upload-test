from fastapi import APIRouter

from my.schemas.social_media_schema import UploadTaskRequest, LoginRequest
from my.services.social_media_ser import social_media_service

social_router = APIRouter(prefix="/social")


@social_router.post("/login")
async def user_login(login: LoginRequest):
    print(f'接收到login:{login}')
    # 将任务添加到队列中
    result = await social_media_service.login(login.platform, login.account_name)
    return {"message": result}


@social_router.post("/upload")
async def video_upload(upload: UploadTaskRequest):
    # 将任务添加到队列中
    result = await social_media_service.upload(upload.platform,upload.account_name)
    return {"message": result}
