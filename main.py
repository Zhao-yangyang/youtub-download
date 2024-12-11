import os
from typing import List, Dict, Optional, Set
import asyncio
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.exceptions import HTTPException
import yt_dlp
from pathlib import Path
from datetime import datetime
import base64
from urllib.parse import unquote
import cv2
from dataclasses import dataclass, field
from collections import deque
import json

app = FastAPI()

# 基础配置
class Config:
    def __init__(self):
        self.DOWNLOAD_DIR = Path("downloads")
        self.DOWNLOAD_DIR.mkdir(exist_ok=True)
        self.load_config()
    
    def load_config(self):
        """从config.json加载配置"""
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.proxy = config.get('proxy', '')
                    self.max_retries = config.get('max_retries', 3)
                    self.retry_delay = config.get('retry_delay', 5)
                    self.max_concurrent = config.get('max_concurrent', 3)
                    self.auto_thumbnail = config.get('auto_thumbnail', True)
            else:
                self.proxy = ''
                self.max_retries = 3
                self.retry_delay = 5
                self.max_concurrent = 3
                self.auto_thumbnail = True
                self.save_config()
        except Exception as e:
            print(f"加载配置失败: {e}")
    
    def save_config(self):
        """保存配置到config.json"""
        try:
            config = {
                'proxy': self.proxy,
                'max_retries': self.max_retries,
                'retry_delay': self.retry_delay,
                'max_concurrent': self.max_concurrent,
                'auto_thumbnail': self.auto_thumbnail
            }
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"保存配置失败: {e}")

# 初始化配置
config = Config()

# 视频下载类
@dataclass
class Video:
    url: str
    format_id: Optional[str] = None
    title: str = ""
    author: str = ""
    duration: str = ""
    file_size: int = 0
    status: str = "pending"
    progress: float = 0
    error: Optional[str] = None
    local_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    def generate_thumbnail(self):
        """生成视频缩略图"""
        if not self.local_path or not os.path.exists(self.local_path):
            return
        
        try:
            thumb_dir = Path("static/thumbnails")
            thumb_dir.mkdir(exist_ok=True)
            
            self.thumbnail_path = str(thumb_dir / f"thumb_{os.path.basename(self.local_path)}.jpg")
            
            cap = cv2.VideoCapture(self.local_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
            ret, frame = cap.read()
            
            if ret:
                cv2.imwrite(self.thumbnail_path, frame)
            
            cap.release()
        except Exception as e:
            print(f"生成缩略图失败: {e}")

# 下载队列管理
@dataclass
class DownloadQueue:
    queue: deque = field(default_factory=deque)
    active_downloads: Dict[str, Video] = field(default_factory=dict)
    max_concurrent: int = 3

    def add_to_queue(self, video: Video) -> bool:
        """添加到下载队列"""
        if video.url in self.active_downloads:
            return False
            
        if len(self.active_downloads) < self.max_concurrent:
            print(f"直接开始下载: {video.url}")  # 添加日志
            self.active_downloads[video.url] = video
            return True
            
        print(f"加入等待队列: {video.url}")  # 添加日志
        self.queue.append(video)
        return False

    def remove_from_active(self, video: Video):
        """从活动下载中移除"""
        if video.url in self.active_downloads:
            print(f"移除活动下载: {video.url}")  # 添加日志
            del self.active_downloads[video.url]
            
            if self.queue and len(self.active_downloads) < self.max_concurrent:
                next_video = self.queue.popleft()
                print(f"从队列启动下载: {next_video.url}")  # 添加日志
                self.active_downloads[next_video.url] = next_video
                asyncio.create_task(download_video(next_video))

# 初始化下载队列和下载列表
download_queue = DownloadQueue()
downloads: List[Video] = []

# 下载函数
async def download_video(video: Video):
    """异步下载视频"""
    def progress_hook(d):
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
            if total > 0:
                video.progress = (downloaded / total) * 100
                video.status = "downloading"
        elif d['status'] == 'finished':
            video.status = "completed"
            video.progress = 100
            video.completed_at = datetime.now()
            if config.auto_thumbnail:
                video.generate_thumbnail()

    try:
        video.status = "pending"
        
        # 基础配置
        ydl_opts = {
            'format': video.format_id or 'best',
            'outtmpl': str(config.DOWNLOAD_DIR / '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 30,
            'extract_flat': True,  # 添加这个选项以支持播放列表
        }
        
        if config.proxy:
            ydl_opts.update({
                'proxy': config.proxy,
                'source_address': '0.0.0.0',
            })
        
        # 先获取视频信息
        try:
            video.status = "fetching"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = await asyncio.to_thread(ydl.extract_info, video.url, download=False)
                    if not info:
                        raise Exception("无法获取视频信息")
                        
                    video.title = info.get('title', '').replace('/', '_')  # 替换非法字符
                    video.author = info.get('uploader', '')
                    video.duration = str(info.get('duration', ''))
                    video.file_size = info.get('filesize', 0)
                    
                    # 设置输出文件名
                    filename = f"{video.title}.{info.get('ext', 'mp4')}"
                    video.local_path = str(config.DOWNLOAD_DIR / filename)
                except Exception as e:
                    raise Exception(f"解析视频信息失败: {str(e)}")
        except Exception as e:
            print(f"获取视频信息失败: {str(e)}")
            raise Exception(f"获取视频信息失败: {str(e)}")

        # 开始下载
        video.status = "downloading"
        retries = 0
        while retries < config.max_retries:
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    await asyncio.to_thread(ydl.download, [video.url])
                    break
            except Exception as e:
                retries += 1
                error_msg = str(e)
                if "Video unavailable" in error_msg:
                    raise Exception("视频不可用或已被删除")
                if retries >= config.max_retries:
                    print(f"下载失败: {error_msg}")
                    raise Exception(f"下载失败(重试{retries}次): {error_msg}")
                video.status = "retrying"
                await asyncio.sleep(config.retry_delay)
                
    except Exception as e:
        video.status = "error"
        video.error = str(e)
        print(f"下载错误: {str(e)}")
    finally:
        download_queue.remove_from_active(video)

# API路由
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "downloads": downloads}
    )

@app.post("/download")
async def start_download(url: str = Form(...), format_id: str = Form(None)):
    try:
        decoded_url = unquote(url)
        # 检查URL格式
        if not decoded_url.startswith('https://www.youtube.com/'):
            raise HTTPException(status_code=400, detail="无效的YouTube链接")
            
        # 检查是否已经在下载列表中
        existing_video = next((v for v in downloads if v.url == decoded_url), None)
        if existing_video:
            # 如果视频已经下载完成或失败，则允许重新下载
            if existing_video.status in ['completed', 'error']:
                downloads.remove(existing_video)
            else:
                raise HTTPException(status_code=400, detail="该视频正在下载中")
            
        # 创建下载任务
        try:
            video = Video(url=decoded_url, format_id=format_id)
            downloads.append(video)
            print(f"添加下载任务: {decoded_url}")
            
            if download_queue.add_to_queue(video):
                print(f"开始下载任务: {decoded_url}")
                asyncio.create_task(download_video(video))
            else:
                print(f"任务加入队列: {decoded_url}")
            
            return {"message": "开始下载", "video": video.url}
        except Exception as e:
            # 如果创建任务失败，从下载列表中移除
            if 'video' in locals() and video in downloads:
                downloads.remove(video)
            print(f"创建下载任务失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"创建下载任务失败: {str(e)}")
            
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"添加下载任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"添加下载任务失败: {str(e)}")

@app.get("/progress/{video_url_b64}")
async def get_progress(video_url_b64: str):
    try:
        # 补全base64字符串的填充
        padding = 4 - (len(video_url_b64) % 4)
        if padding != 4:
            video_url_b64 += '=' * padding
            
        # 替换特殊字符
        video_url_b64 = video_url_b64.replace('-', '+').replace('_', '/')
        
        # 解码URL
        video_url = unquote(base64.b64decode(video_url_b64.encode()).decode())
        
        video = next((v for v in downloads if v.url == video_url), None)
        
        if not video:
            print(f"未找到下载任务: {video_url}")
            return {"status": "not_found", "progress": 0}
            
        # 检查是否在活动下载中
        is_active = video.url in download_queue.active_downloads
        is_queued = video in download_queue.queue
        
        response = {
            "status": video.status,
            "progress": video.progress,
            "title": video.title,
            "error": video.error,
            "author": video.author,
            "duration": video.duration,
            "file_size": video.file_size,
            "local_path": video.local_path,
            "filename": os.path.basename(video.local_path) if video.local_path else None,
            "is_active": is_active,
            "is_queued": is_queued
        }
        
        print(f"进度更新 - {video_url}: {response['status']} {response['progress']}%")
        return response
    except Exception as e:
        print(f"获取进度失败: {str(e)}")
        return {"status": "error", "progress": 0, "message": str(e)}

@app.get("/config")
async def get_config():
    return {
        "proxy": config.proxy,
        "max_retries": config.max_retries,
        "retry_delay": config.retry_delay,
        "max_concurrent": config.max_concurrent,
        "auto_thumbnail": config.auto_thumbnail
    }

@app.post("/config")
async def update_config(
    proxy: str = Form(None),
    max_retries: int = Form(None),
    retry_delay: int = Form(None),
    max_concurrent: int = Form(None),
    auto_thumbnail: bool = Form(None)
):
    if proxy is not None:
        config.proxy = proxy
    if max_retries is not None:
        config.max_retries = max_retries
    if retry_delay is not None:
        config.retry_delay = retry_delay
    if max_concurrent is not None:
        config.max_concurrent = max_concurrent
        download_queue.max_concurrent = max_concurrent
    if auto_thumbnail is not None:
        config.auto_thumbnail = auto_thumbnail
    
    config.save_config()
    return {"message": "配置已更新"}

# 静态文件配置
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/downloads", StaticFiles(directory="downloads", html=True), name="downloads")
templates = Jinja2Templates(directory="templates") 