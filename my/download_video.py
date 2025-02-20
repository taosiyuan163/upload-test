from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import httpx

router = APIRouter()

async def fetch_video_stream(url: str):
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream("GET", url) as response:
                if response.status_code != 200:
                    raise HTTPException(status_code=response.status_code, detail="Failed to fetch video")

                # 流式传输数据
                async for chunk in response.aiter_bytes():
                    yield chunk
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"HTTP error occurred: {str(e)}")


@router.get("/download_video/")
async def download_video(video_url: str):
    try:
        # 验证 URL 格式
        if not video_url.startswith("http://127.0.0.1:8080/tasks/"):
            raise HTTPException(status_code=400, detail="Invalid video URL format")

        # 返回流式响应
        return StreamingResponse(
            fetch_video_stream(video_url),
            media_type="video/mp4",
            headers={"Content-Disposition": f"attachment; filename=video.mp4"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))