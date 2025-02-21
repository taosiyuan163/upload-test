import os
from pathlib import Path

import httpx

from my.gen.video import submit_create_videos_task, get_or_create_user_video_dir
from my.schemas.social_media_schema import UploadTaskRequest
from my.utils.data_util import get_douyin_cookie_path
from uploader.douyin_uploader.main import douyin_setup, DouYinVideo
from utils.base_social_media import SOCIAL_MEDIA_DOUYIN
from utils.files_times import generate_schedule_time_next_day, get_title_and_hashtags

# 获取当前脚本所在目录的绝对路径，并转换为Path对象
current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
# 获取上一级目录的路径
my_dir = current_dir.parent
# 获取上两级目录的路径
root_dir = my_dir.parent


class SocialMediaService:
    """
    和社交媒体交互的服务
    """

    def __init__(self):
        # 将root_dir转换为Path对象后，再进行路径拼接
        self.coolies_dir = root_dir / "cookies" / "douyin_uploader"



    def get_account_cookie_path(self, account_name):
        return self.coolies_dir / f"{account_name}.json"

    async def login(self, platform, account_name):
        get_or_create_user_video_dir(account_name)

        if platform == SOCIAL_MEDIA_DOUYIN:
            account_file = get_douyin_cookie_path(account_name)
            cookie_setup = await douyin_setup(str(account_file), handle=True)
            print(f'登录成功，account_name：{account_name}，cookie_setup：{cookie_setup}')
        else:
            raise Exception(f"不支持的平台：{platform}")
        return cookie_setup

    # 处理任务的协程
    async def upload(self, platform, account_name):
        account_file = self.get_account_cookie_path(account_name)

        video_folder_path = r'E:\projects\upload-test\\videos'
        if platform == SOCIAL_MEDIA_DOUYIN:
            # 将任务放入队列
            result = await self.upload_douyin(account_file, video_folder_path)
        else:
            raise Exception(f"不支持的平台：{platform}")

        return result

    async def create_videos(self,
                            aclient: httpx.AsyncClient,
                            subject,
                            account_name):

        return await submit_create_videos_task(aclient, subject, account_name)


# 创建服务实例
social_media_service = SocialMediaService()
