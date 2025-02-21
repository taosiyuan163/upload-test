import asyncio
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from typing import Optional, List

from my.api.social_media_api import social_router
from my.daemon import process_gen_video_tasks


class FastAPIApp:
    def __init__(
        self,
        title: str = "title",
        description: str = "description",
        version: str = "1.0.0",
        debug: bool = False,
        cors_allowed_origins: Optional[List[str]] = None,
    ):
        """
        Initialize the FastAPI application.

        Args:
            title (str): The title of the application.
            description (str): The description of the application.
            version (str): The version of the application.
            debug (bool): Whether to run the application in debug mode.
            cors_allowed_origins (Optional[List[str]]): List of allowed origins for CORS.
        """
        self.title = title
        self.description = description
        self.version = version
        self.debug = debug
        self.cors_allowed_origins = cors_allowed_origins or ["*"]

        # Initialize the FastAPI app
        self.app = self._create_app()

    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """
        Lifespan context manager for managing the lifecycle of the FastAPI app.
        """
        try:
            client = httpx.AsyncClient(
                timeout=httpx.Timeout(10.0),  # 设置超时
                limits=httpx.Limits(max_connections=100)  # 设置连接池大小
            )
            app.state.aclient = client
            logger.info("AsyncClient initialized")
            yield
        except Exception as e:
            logger.error(f"Failed to initialize AsyncClient: {e}")
            raise
        finally:
            if hasattr(app.state, "aclient"):
                await app.state.aclient.aclose()
                logger.info("AsyncClient closed")

    def _create_app(self) -> FastAPI:
        """
        Create and configure the FastAPI application.

        Returns:
            FastAPI: The configured FastAPI application instance.
        """
        # Initialize FastAPI app with lifespan
        app = FastAPI(
            title=self.title,
            description=self.description,
            version=self.version,
            debug=self.debug,
            lifespan=self.lifespan,
        )

        # Add CORS middleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=self.cors_allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Add exception handlers
        self._add_exception_handlers(app)

        return app

    def _add_exception_handlers(self, app: FastAPI) -> None:
        """
        Add custom exception handlers to the FastAPI app.

        Args:
            app (FastAPI): The FastAPI application instance.
        """
        @app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "message": f"请求数据无效:{request}",
                    "errors": exc.errors(),
                },
            )

        @app.exception_handler(Exception)
        async def generic_exception_handler(request: Request, exc: Exception):
            logger.error(f"Unhandled exception: {exc}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": 500,
                    "message": f"内部错误，请求：{request}",
                },
            )

    def add_event(self, app: FastAPI):
        # 自动处理生成好的视频
        @app.on_event("startup")
        async def startup_event():
            asyncio.create_task(process_gen_video_tasks())
        pass

    def add_router(self, router):
        self.app.include_router(router, prefix='/api/v1')

    def get_app(self) -> FastAPI:
        """
        Get the FastAPI application instance.

        Returns:
            FastAPI: The FastAPI application instance.
        """
        return self.app


# Example usage
if __name__ == "__main__":
    from fastapi import APIRouter


    # Initialize the FastAPI app
    app_instance = FastAPIApp(
        title="自动化测试工程",
        description="上传内容",
        version="1.0.0",
        debug=True
        # cors_allowed_origins=["http://localhost:3000"],  # Allow specific origins
    )

    # 定义路由器列表
    routers = [
        social_router
    ]

    # 注册所有路由器
    for router in routers:
        app_instance.add_router(router)

    # Get the FastAPI app
    app = app_instance.get_app()

    # Run the app (for development)
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)