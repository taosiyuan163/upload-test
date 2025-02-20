# 用于存储任务的队列
import asyncio
import os
import subprocess

upload_task_queue = asyncio.Queue()


# 处理任务的协程
async def process_tasks():
    current_dir = os.path.dirname(os.path.abspath(__file__))  # 获取当前脚本所在目录的绝对路径
    cli_main_path = os.path.join(os.path.dirname(current_dir), "cli_main.py")  # 上一级目录中的cli_main.py路径

    while True:
        # 从队列中获取任务
        task = await upload_task_queue.get()
        platform, account_name, action, video_path = task

        if action == 'upload':
            options = ['-pt', 0]
        else:
            options = ''

        try:
            # 调用cli_main.py脚本
            command = ["python", cli_main_path, platform, account_name, action, video_path] + options
            process = await asyncio.create_subprocess_exec(*command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                print(f"Task failed: {stderr.decode()}")
            else:
                print(f"Task succeeded: {stdout.decode()}")

        except Exception as e:
            print(f"Error processing task: {e}")

        finally:
            # 标记任务完成
            upload_task_queue.task_done()
            await asyncio.sleep(3)
