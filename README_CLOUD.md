# 云服务器部署说明

## 问题描述

原始的 `main.py` 和 `app.py` 使用 PyAudio 直接从服务器的音频设备（麦克风）捕获音频。这在云服务器上会失败，因为：
- 云服务器通常没有物理音频设备
- 即使有虚拟音频设备，也无法访问用户的麦克风

## 解决方案

创建了新的架构，将音频捕获从服务器端移到客户端（浏览器）：

### 新增文件

1. **audio_processor.py** - 音频处理模块
   - 不依赖 PyAudio
   - 接收已录制的音频文件进行处理
   - 包含语音识别和AI分析功能
   - 适用于云服务器环境

2. **app_web.py** - 新的 Streamlit 应用
   - 使用 `streamlit-audiorecorder` 在浏览器中录音
   - 支持音频文件上传（WAV、MP3、M4A）
   - 自动转换音频格式
   - 保留原有的文件管理和日历功能

### 架构对比

#### 旧架构（app.py + main.py）
```
[服务器麦克风] → [PyAudio] → [阿里云ASR] → [DeepSeek AI]
                    ❌ 云服务器上不可用
```

#### 新架构（app_web.py + audio_processor.py）
```
[浏览器麦克风/文件] → [Streamlit] → [音频处理器] → [阿里云ASR] → [DeepSeek AI]
                                    ✅ 云服务器兼容
```

## 使用方法

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

新增的依赖：
- `streamlit-audiorecorder` - 浏览器录音组件
- `pydub` - 音频格式转换

移除的依赖：
- `pyaudio` - 不再需要（已从 requirements.txt 移除）

### 2. 运行新应用

```bash
streamlit run app_web.py
```

### 3. 使用功能

#### 方法一：浏览器录音（推荐）
1. 在侧边栏点击"开始录音"按钮
2. 允许浏览器访问麦克风
3. 开始说话
4. 点击"停止录音"按钮
5. 点击"处理录音"按钮
6. 等待处理完成，查看结果

#### 方法二：上传音频文件
1. 在侧边栏选择"选择音频文件"
2. 上传 WAV/MP3/M4A 格式的音频文件
3. 点击"处理音频"按钮
4. 等待处理完成，查看结果

### 4. 查看历史记录

- 点击侧边栏的"📅 日历"按钮
- 选择日期查看该日的所有录音
- 点击文件查看详细内容

## 技术细节

### 音频格式要求

阿里云语音识别服务要求：
- 采样率：16000 Hz
- 声道：单声道（Mono）
- 格式：PCM/WAV

`app_web.py` 会自动转换上传的音频文件以符合要求。

### 文件结构

```
data/
├── TXT/          # 语音识别结果（文本）
├── MD/           # AI分析结果（Markdown）
└── WAV/          # 录音文件
```

### API 配置

需要配置以下 API：

1. **阿里云语音识别**
   - API Key: 在 `audio_processor.py` 中配置
   - 默认使用 `fun-asr-realtime` 模型

2. **DeepSeek AI**
   - API Key: 在 `audio_processor.py` 中配置
   - 用于文本分析和文件名生成

## 对比旧版本

### 优势
✅ **云服务器兼容** - 不需要服务器音频设备  
✅ **更灵活** - 支持多种音频格式  
✅ **更安全** - 音频在客户端捕获，不经过中间服务器  
✅ **易部署** - 少一个依赖（PyAudio 编译复杂）  
✅ **跨平台** - 浏览器录音在所有平台都可用  

### 保留功能
✅ 实时语音识别（处理上传的音频）  
✅ AI 智能分析  
✅ 文件管理和历史记录  
✅ 日历视图  
✅ 自动文件命名  

### 限制
⚠️ 不支持真正的"实时"流式识别（因为音频需要先在浏览器录制完成）  
⚠️ 需要用户手动点击"处理"按钮  

## 迁移指南

如果你已经使用旧版本（app.py）：

1. **保留数据**
   ```bash
   # 你的 data/ 文件夹中的数据会被保留
   # 新版本完全兼容旧版本的数据格式
   ```

2. **切换到新版本**
   ```bash
   # 停止旧版本
   # Ctrl+C 停止 streamlit run app.py
   
   # 启动新版本
   streamlit run app_web.py
   ```

3. **更新依赖**
   ```bash
   pip install streamlit-audiorecorder pydub
   # 可选：卸载 pyaudio
   pip uninstall pyaudio
   ```

## 故障排除

### 1. audiorecorder 组件无法使用

如果 `streamlit-audiorecorder` 无法安装或使用，应用会自动切换到文件上传模式。

```bash
# 尝试重新安装
pip install --upgrade streamlit-audiorecorder
```

### 2. 音频格式转换失败

确保安装了 `pydub` 及其依赖：

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
# 下载 ffmpeg 并添加到 PATH
```

### 3. 语音识别失败

检查：
- 阿里云 API Key 是否正确
- 网络连接是否正常
- 音频文件格式是否正确（16kHz，单声道）

### 4. AI 分析失败

检查：
- DeepSeek API Key 是否正确
- 网络连接是否正常
- `system.txt` 文件是否存在

## 部署建议

### 本地开发
```bash
streamlit run app_web.py
```

### 云服务器部署
```bash
# 使用 nohup 后台运行
nohup streamlit run app_web.py --server.port 8501 --server.address 0.0.0.0 &

# 或使用 systemd/supervisor 管理进程
```

### Docker 部署
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y ffmpeg

EXPOSE 8501
CMD ["streamlit", "run", "app_web.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## 支持与反馈

如有问题，请检查：
1. Python 版本 >= 3.7
2. 所有依赖已正确安装
3. API Keys 已正确配置
4. 网络连接正常
