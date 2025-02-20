import os
from pathlib import Path

from my.daemon import upload_task_queue
from my.schemas.social_media_schema import UploadTaskRequest
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

    async def upload_douyin(self, account_file, video_folder_path):
        # filepath = Path(BASE_DIR) / "videos"
        # account_file = Path(BASE_DIR / "cookies" / "douyin_uploader" / "account.json")
        # 获取视频目录
        folder_path = Path(video_folder_path)
        # 获取文件夹中的所有文件
        files = list(folder_path.glob("*.mp4"))
        file_num = len(files)
        publish_datetimes = generate_schedule_time_next_day(file_num, 1, daily_times=[16])
        cookie_setup = await douyin_setup(account_file, handle=False)
        #抖音设置完毕,account_file:E:\projects\upload-test\cookies\douyin_uploader\tsy1.json,cookie_setup=True,publish_datetimes=[datetime.datetime(2025, 2, 21, 16, 0)]
        print(
            f'抖音设置完毕,account_file:{account_file},cookie_setup={cookie_setup},publish_datetimes={publish_datetimes}')
        for index, file in enumerate(files):
            title, tags = get_title_and_hashtags(str(file))
            thumbnail_path = file.with_suffix('.png')
            # 打印视频文件名、标题和 hashtag
            # 暂时没有时间修复封面上传，故先隐藏掉该功能
            # if thumbnail_path.exists():
            # app = DouYinVideo(title, file, tags, publish_datetimes[index], account_file, thumbnail_path=thumbnail_path)
            # else:
            print(f'视频文件名：{file},标题：{title},Hashtag：{tags}')
            app = DouYinVideo(title, file, tags, publish_datetimes[index], account_file)
            result = await app.main()
            print(f'【{title}】发布完成,{result}')

        print(f'【{account_file}】发布完成')

    def get_account_cookie_path(self, account_name):
        return self.coolies_dir / f"{account_name}.json"

    async def login(self, platform, account_name):
        if platform == SOCIAL_MEDIA_DOUYIN:
            account_file = self.get_account_cookie_path(account_name)
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


# 创建服务实例
social_media_service = SocialMediaService()
