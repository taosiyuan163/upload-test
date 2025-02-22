import traceback
import httpx
from loguru import logger

# 假设这些是从'my.gen.video'模块中导入的函数
# 确保'my.gen.video'模块中定义了'download_videos'和'upload_douyin'函数
from my.gen.video import download_videos, upload_douyin

videos_url_list = ['http://127.0.0.1:8080/tasks/a12e54ae-fd35-4ca3-a1a6-68971c031ea9/final-1.mp4']

async def a(aclient: httpx.AsyncClient):
    uid= 'tsy1'
    title='测试视频1'
    tags=['美食','餐饮']
    if videos_url_list:
        try:
            videos_dir = await download_videos(aclient, uid,
                                               videos_url_list,
                                               title, tags)

            # await upload_douyin(uid, videos_dir)
        except Exception as e:
            logger.error(f"发布视频时异常: {e}\n{traceback.format_exc()}")

# 使用异步函数进行调用
async def main():
    async with httpx.AsyncClient() as client:
        await a(client)

# 运行异步主函数
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())