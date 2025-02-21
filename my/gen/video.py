import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

import aiofiles
import httpx
from fastapi import HTTPException

from my.config import VIDEO_GEN_URL, VIDEO_GEN_SEARCH_TASK_URL
from my.schemas.task import GenVideosTask
from my.utils.data_util import get_douyin_cookie_path
from uploader.douyin_uploader.main import douyin_setup, DouYinVideo
from utils.files_times import generate_schedule_time_next_day, get_title_and_hashtags

# uid->Task
gen_video_tasks: Dict[str, GenVideosTask] = {}

# E:\projects\upload-test\my\utils
current_dir = Path(os.path.dirname(os.path.abspath(__file__)))


def check_task(uid):
    if uid in gen_video_tasks:
        raise Exception(f"用户：{uid}任务还未结束，无法提交请求")


def add_task(uid, task_id):
    if uid is None:
        raise Exception(f"用户名为空")
    if task_id is None:
        raise Exception(f"用户：{uid}的task_id为空")

    gen_video_tasks[uid] = task_id
    print(f'加入用户任务id:{task_id}')


def get_or_create_user_video_dir(uid):
    # 构建目标目录路径：上一级目录下的gen/videos/uid
    target_dir = current_dir / "videos" / uid

    if not target_dir.exists():
        # 创建目录，如果目录已经存在则不会抛出异常
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f'成功创建用户{uid}目录: {target_dir}')

    return target_dir


async def submit_create_videos_task(aclient: httpx.AsyncClient, subject,
                                    uid,title,tags):
    check_task(uid)

    payload = {
        "video_subject": subject,
        "video_script": "",
        "video_terms": "",
        "video_aspect": "9:16",  # 抖音比例
        "video_concat_mode": "random",
        "video_transition_mode": "None",  # 必填
        "video_clip_duration": 3,  # 视频切片最大时长
        "video_count": 1,
        "video_source": "pexels",
        "video_materials": None,
        "video_language": "",
        "voice_name": "zh-CN-XiaoxiaoNeural-Female",  # 人声
        "voice_volume": 1.0,
        "voice_rate": 1.0,
        "bgm_type": "random",
        "bgm_file": "",
        "bgm_volume": 0.2,
        "subtitle_enabled": True,
        "subtitle_position": "bottom",
        "custom_position": 70.0,
        "font_name": "MicrosoftYaHeiBold.ttc",
        "text_fore_color": "#FFFFFF",
        "text_background_color": True,
        "font_size": 60,
        "stroke_color": "#000000",
        "stroke_width": 1.5,
        "n_threads": 2,
        "paragraph_number": 1  # 生成视频脚本的段落个数
    }

    start_time = time.time()

    response = await aclient.post(VIDEO_GEN_URL, json=payload, timeout=300)

    # Check response status code
    if response.status_code == 200:
        # Parse response data
        response_data = response.json()
        if response_data['status'] == 200:
            # Log request and response
            end_time = time.time()
            duration = end_time - start_time
            print(f"请求成功: {payload} , 返回: {response_data}，耗时:{duration}")
            # return response_data, duration
        else:
            msg = f'创建视频失败,请求:{payload},返回:{response_data}'
            print(msg, response_data)
            raise HTTPException(status_code=response.status_code, detail=msg)
    else:
        msg = f'创建视频失败,请求:{payload},返回:{response.status_code}'
        print(msg, response.status_code)
        raise HTTPException(status_code=response.status_code, detail=msg)

    task_id = response_data['data']['task_id']
    task = GenVideosTask(uid, task_id, start_time,title,tags)
    add_task(uid, task)

    return response


async def upload_douyin(account_name, video_folder_path):
    account_file = get_douyin_cookie_path(account_name)
    # 获取视频目录
    folder_path = Path(video_folder_path)
    # 获取文件夹中的所有文件
    files = list(folder_path.glob("*.mp4"))
    file_num = len(files)
    publish_datetimes = generate_schedule_time_next_day(file_num, 1, daily_times=[16])
    cookie_setup = await douyin_setup(account_file, handle=False)
    # 抖音设置完毕,account_file:E:\projects\upload-test\cookies\douyin_uploader\tsy1.json,cookie_setup=True,publish_datetimes=[datetime.datetime(2025, 2, 21, 16, 0)]
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


async def gen_videos_url(aclient: httpx.AsyncClient, task: GenVideosTask):
    start_time = time.time()
    task_id = task.task_id

    elapsed_time = start_time - task.submit_time

    # 判断是否超时
    if elapsed_time > 300:  # 300 seconds = 5 minutes
        print(f'超时！视频生成任务：{task_id} 超时。取消该任务！')
        # 使用 pop 方法移除指定键的元素，并提供一个默认值以防键不存在
        gen_video_tasks.pop(task.user_id, None)
        return

    response = await aclient.get(f"{VIDEO_GEN_SEARCH_TASK_URL}/{task_id}")

    # Check response status code
    if response.status_code == 200:
        # Parse response data
        response_data = response.json()
        if response_data['status'] == 200:
            end_time = time.time()
            # duration = end_time - start_time
            # print(f"查询视频生成任务: {task_id} , 返回: {response_data}，耗时:{duration}")
            # return response_data, duration
        else:
            msg = f'查询视频生成任务失败:{task_id},返回:{response_data}'
            print(msg, response_data)
            raise HTTPException(status_code=response.status_code, detail=msg)
    else:
        msg = f'查询视频生成任务失败:{task_id},返回:{response.status_code}'
        print(msg, response.status_code)
        raise HTTPException(status_code=response.status_code, detail=msg)

    data = response_data['data']
    if data['state'] == 1:
        # ["http://127.0.0.1:8080/tasks/d9090137-c057-4295-8520-cde96dceccc7/final-1.mp4"]
        videos_url_list = data['videos']
        print(f'视频生成完成,共计{len(videos_url_list)}个')
        return videos_url_list
    else:
        progress = data['progress']
        print(f'视频生成中，进度{progress}%')

async def write_video_text_des(save_dir_path,txt_name,title,tags):

    txt_filepath = os.path.join(save_dir_path, txt_name)
    #组装标签
    formatted_tags = " ".join([f"#{tag}" for tag in tags])

    async with aiofiles.open(txt_filepath, 'w') as f:
        await f.write(title)
        await f.write(formatted_tags)

    print(f'视频描述文件写入成功，title：{title}，tags：{formatted_tags}')
async def download_videos(aclient: httpx.AsyncClient,
                          uid: str,
                          urls: List[str],title,tags):
    # 获取当前时间并格式化为年月日时分秒
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    user_videos_dir = get_or_create_user_video_dir(uid)
    save_dir_path = os.path.join(user_videos_dir, current_time)

    # 目录存在就报错
    os.makedirs(save_dir_path, exist_ok=False)

    downloaded_files = []

    for url in urls:
        # 获取文件名
        filename = url.split('/')[-1]
        filepath = os.path.join(save_dir_path, filename)

        #提取并创建视频描述的文件
        filename_without_extension = os.path.splitext(filename)[0]
        txt_name = f'{filename_without_extension}.txt'
        await write_video_text_des(save_dir_path,txt_name,title,tags)

        async with aclient.stream('GET', url) as response:
            response.raise_for_status()  # 检查请求是否成功

            # 使用 aiofiles 异步写入文件
            async with aiofiles.open(filepath, 'wb') as f:
                async for chunk in response.aiter_bytes():
                    if chunk:  # 如果块不为空
                        await f.write(chunk)

        print(f'{filename} 下载完毕')
        downloaded_files.append(filepath)

    return downloaded_files


async def process_gen_video_tasks(aclient: httpx.AsyncClient):
    while True:
        for uid, task in gen_video_tasks:
            videos_url_list = await gen_videos_url(aclient, task)

            #todo 内容和标签
            if videos_url_list:
                downloaded_files = await download_videos(aclient, uid,
                                                         videos_url_list,
                                                         task.title,task.tags)

                for file in downloaded_files:
                    #todo title,tags对应各视频上
                    await upload_douyin(uid, file)
        #
        # task = await upload_task_queue.get()
        # platform, account_name, action, video_path = task
        #
        # if action == 'upload':
        #     options = ['-pt', 0]
        # else:
        #     options = ''
        #
        # try:
        #     # 调用cli_main.py脚本
        #     command = ["python", cli_main_path, platform, account_name, action, video_path] + options
        #     process = await asyncio.create_subprocess_exec(*command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #     stdout, stderr = await process.communicate()
        #
        #     if process.returncode != 0:
        #         print(f"Task failed: {stderr.decode()}")
        #     else:
        #         print(f"Task succeeded: {stdout.decode()}")
        #
        # except Exception as e:
        #     print(f"Error processing task: {e}")
        #
        # finally:
        #     # 标记任务完成
        #     upload_task_queue.task_done()
        #     await asyncio.sleep(3)
