from my.daemon import upload_task_queue
from my.schemas.social_media_schema import UploadTaskRequest


class SocialMediaService:
    """
    和社交媒体交互的服务
    """

    def __init__(self):
        self.a = ""

    # 处理任务的协程
    async def upload(self, task: UploadTaskRequest):
        # 将任务放入队列
        await upload_task_queue.put(task)
        print('任务入队成功', task)


# 创建服务实例
social_media_service = SocialMediaService()
