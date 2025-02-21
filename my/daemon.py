# 用于存储任务的队列
import asyncio
import os
import subprocess

# upload_task_queue = asyncio.Queue()



current_dir = os.path.dirname(os.path.abspath(__file__))  # 获取当前脚本所在目录的绝对路径
cli_main_path = os.path.join(os.path.dirname(current_dir), "cli_main.py")  # 上一级目录中的cli_main.py路径


# 处理任务的协程

