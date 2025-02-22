import asyncio
import os
import traceback
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request, APIRouter
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from typing import Optional, List

from my.api.social_media_api import social_router
from my.gen.video import process_gen_video_tasks


class FastAPIApp:
    def __init__(
        self,
        title: str = "title",
        description: str = "description",
        version: str = "1.0.0",
        debug: bool = False,
        cors_allowed_origins: Optional[List[str]] = None,
        http_timeout: float = 10.0,
        http_max_connections: int = 100,
        host: str = "0.0.0.0",
        port: int = 8000,
        routers: Optional[List[APIRouter]] = None,
    ):
        self.title = title
        self.description = description
        self.version = version
        self.debug = debug
        self.cors_allowed_origins = cors_allowed_origins or ["*"]
        self.http_timeout = http_timeout
        self.http_max_connections = http_max_connections
        self.host = host
        self.port = port
        self.routers = routers or []

        # Initialize the FastAPI app
        self.app = self._create_app()

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        try:
            # 初始化 AsyncClient
            client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.http_timeout),
                limits=httpx.Limits(max_connections=self.http_max_connections)
            )
            app.state.aclient = client
            logger.info("AsyncClient initialized")

            # 启动视频任务处理
            logger.info("Starting up video task processing")
            task = asyncio.create_task(process_gen_video_tasks(app.state.aclient))
            app.state.video_task = task  # 保存任务引用

            yield  # 应用程序运行

        except Exception as e:
            logger.error(f"Failed to initialize AsyncClient or start video task: {e}")
            raise
        finally:
            # 关闭 AsyncClient
            if hasattr(app.state, "aclient"):
                await app.state.aclient.aclose()
                logger.info("AsyncClient closed")

            # 取消视频任务（如果需要）
            if hasattr(app.state, "video_task"):
                app.state.video_task.cancel()
                try:
                    await app.state.video_task
                except asyncio.CancelledError:
                    logger.info("Video task cancelled")

    def _create_app(self) -> FastAPI:
        # 先初始化 FastAPI 应用
        app = FastAPI(
            title=self.title,
            description=self.description,
            version=self.version,
            debug=self.debug,
            lifespan=self.lifespan,
        )

        # 添加 CORS 中间件
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.cors_allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # 添加异常处理器
        self._add_exception_handlers(app)

        # 注册所有路由器
        for router in self.routers:
            app.include_router(router, prefix='/api/v1')  # 直接使用 app 注册路由

        # 将 app 赋值给 self.app
        self.app = app
        return app

    def _add_exception_handlers(self, app: FastAPI) -> None:
        @app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            # 读取请求体
            body = await request.body()
            try:
                # 尝试将请求体解析为json格式
                body_str = body.decode("utf-8")
            except UnicodeDecodeError:
                body_str = str(body)

            logger.error(f"请求数据：{body_str}，错误: {exc}\n{traceback.format_exc()}")
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "message": "请求数据无效",
                    "errors": exc.errors(),
                },
            )

        @app.exception_handler(Exception)
        async def generic_exception_handler(request: Request, exc: Exception):
            # 读取请求体
            body = await request.body()
            try:
                # 尝试将请求体解析为json格式
                body_str = body.decode("utf-8")
            except UnicodeDecodeError:
                body_str = str(body)

            # 记录完整的错误堆栈信息
            logger.error(f"请求数据：{body_str}，内部错误: {exc}\n{traceback.format_exc()}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": 500,
                    "message": "内部错误",
                    "detail": str(exc),  # 返回错误的详细信息
                },
            )

    def add_router(self, router):
        self.app.include_router(router, prefix='/api/v1')

    def get_app(self) -> FastAPI:
        return self.app


# Example usage
if __name__ == "__main__":
    from fastapi import APIRouter

    # Initialize the FastAPI app
    app_instance = FastAPIApp(
        title="自动化测试工程",
        description="上传内容",
        version="1.0.0",
        debug=True,
        host="0.0.0.0",
        port=8000,
        routers=[social_router],
    )

    # Get the FastAPI app
    app = app_instance.get_app()

    # Run the app (for development)
    import uvicorn
    uvicorn.run(app, host=app_instance.host, port=app_instance.port)