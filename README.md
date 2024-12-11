# YouTube Video Downloader

一个基于FastAPI和yt-dlp的YouTube视频下载工具,支持批量下载、进度显示、代理设置等功能。

## 主要特性

### 核心功能
- 支持YouTube视频链接解析和下载
- 支持批量下载(每行一个链接)
- 实时显示下载进度和状态
- 视频预览和本地播放
- 自动获取视频信息(标题、作者、时长等)

### 高级功能
- 异步下载处理
- 并发下载控制
- 智能队列管理
- 自动重试机制
- 代理服务器支持
- 基础错误处理

## 技术架构

### 后端
- Web框架: FastAPI
- 视频下载: yt-dlp
- 异步处理: asyncio
- 视频处理: opencv-python

### 前端
- 模板引擎: Jinja2
- UI框架: TailwindCSS
- 交互处理: 原生JavaScript

### 数据存储
- 配置管理: JSON
- 文件存储: 本地文件系统

## 项目结构
```
project/
├── static/          # 静态资源
│   ├── css/         # 样式文件
│   └── js/          # JavaScript文件
├── templates/       # 页面模板
│   ├── components/  # 可复用组件
│   ├── index.html   # 主页面
│   ├── history.html # 历史记录
│   └── settings.html# 设置页面
├── downloads/       # 下载文件存储
├── config.json      # 配置文件
├── main.py         # 程序入口
├── .env            # 环境配置
└── README.md       # 项目文档
```

## 快速开始

### 环境要求
- Python 3.8+
- pip包管理器
- 网络连接

### 安装步骤

1. 克隆项目
```bash
git clone <repository-url>
cd youtube-downloader
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 创建必要目录
```bash
mkdir -p static/{css,js} downloads
```

4. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件配置以下参数:
PROXY=http://127.0.0.1:7890  # 代理服务器(可选)
MAX_RETRIES=3                # 最大重试次数
RETRY_DELAY=5                # 重试延迟(秒)
MAX_CONCURRENT=3             # 最大并发下载数
DOWNLOAD_PATH=downloads      # 下载目录
```

### 启动服务

1. 开发模式
```bash
uvicorn main:app --reload --port 8000
```

2. 生产模式
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000 即可使用

## 使用指南

### 基本使用
1. 在输入框中粘贴YouTube视频链接(支持批量,每行一个)
2. 点击"开始下载"按钮
3. 在下方列表查看下载进度
4. 下载完成后可预览或下载到本地

### 高级设置
在设置面板中可配置:
- 代理服务器
- 最大重试次数
- 重试延迟时间
- 最大并发下载数
- 缩略图生成选项

## 开发状态

### 已完成功能
- [x] 核心下载功能
- [x] 批量下载支持
- [x] 进度显示
- [x] 代理设置
- [x] 并发控制
- [x] 视频预览
- [x] 错误处理
- [x] 下载历史

### 开发中功能
- [ ] 视频格式选择
- [ ] 下载速度限制
- [ ] 历史记录管理
- [ ] 批量下载优化
- [ ] 预览体验优化

### 规划中功能
- [ ] 自动更新检查
- [ ] 数据导出功能
- [ ] 系统托盘运行
- [ ] 队列持久化
- [ ] 自定义下载目录
- [ ] 视频标签管理
- [ ] 下载通知
- [ ] 断点续传

## 贡献指南

欢迎提交Issue和Pull Request。在贡献代码前请先阅读以下指南:

1. Fork本仓库
2. 创建特性分支
3. 提交变更
4. 创建Pull Request

## 许可证

本项目采用MIT许可证 - 详见 [LICENSE](LICENSE) 文件