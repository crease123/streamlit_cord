# 快速开始指南

## ✅ 问题已解决

原始代码使用 PyAudio 从服务器本地捕获音频，这在云服务器上不可用。新版本改为从浏览器捕获音频，完全兼容云服务器环境。

## 🚀 立即开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

**注意：** 如果你之前安装过 PyAudio，可以将其卸载（不再需要）：
```bash
pip uninstall pyaudio
```

### 2. 运行新版应用

```bash
streamlit run app_web.py
```

应用将在浏览器中打开（默认地址：http://localhost:8501）

### 3. 开始使用

#### 选项 A：浏览器录音（推荐）

1. 在侧边栏点击 "开始录音" 按钮
2. 允许浏览器访问麦克风
3. 开始说话
4. 点击 "停止录音"
5. 点击 "处理录音" 按钮
6. 等待处理完成

#### 选项 B：上传音频文件

1. 在侧边栏选择 "选择音频文件"
2. 上传 WAV/MP3/M4A 格式的音频
3. 点击 "处理音频" 按钮
4. 等待处理完成

## 📊 测试结果

运行测试脚本验证功能：

```bash
python test_audio_processor.py
```

测试结果：
```
✅ 依赖导入测试: 通过
✅ 文件结构测试: 通过
✅ 功能测试: 通过
✅ 可以在云服务器上运行
```

## 🆚 新旧版本对比

### 旧版本（app.py + main.py）
- ❌ 依赖 PyAudio
- ❌ 需要服务器音频设备
- ❌ 云服务器不可用
- ❌ 安装复杂（PyAudio 编译困难）

### 新版本（app_web.py + audio_processor.py）
- ✅ 不依赖 PyAudio
- ✅ 不需要服务器音频设备
- ✅ 云服务器完全兼容
- ✅ 安装简单
- ✅ 支持多种音频格式

## 📁 文件说明

### 新增文件

- `app_web.py` - 新的 Streamlit 应用（使用浏览器录音）
- `audio_processor.py` - 音频处理模块（不依赖 PyAudio）
- `test_audio_processor.py` - 测试脚本
- `README_CLOUD.md` - 详细文档
- `QUICKSTART.md` - 本文件

### 保留文件

- `app.py` - 旧版应用（保留但不推荐使用）
- `main.py` - 旧版录音脚本（保留但不推荐使用）
- `data/` - 数据文件夹（新旧版本兼容）
- `system.txt` - AI 系统提示

## 🔧 配置

### API 密钥

在 `audio_processor.py` 中配置：

1. **阿里云语音识别 API**
   ```python
   dashscope.api_key = 'your-dashscope-api-key'
   ```

2. **DeepSeek AI API**
   ```python
   client = OpenAI(
       api_key="your-deepseek-api-key",
       base_url="https://api.deepseek.com"
   )
   ```

### 系统提示

编辑 `system.txt` 文件自定义 AI 的行为：

```
你是一个智能助手，帮助用户分析和处理输入的文本。
```

## 🌐 云服务器部署

### 方法 1：直接运行

```bash
streamlit run app_web.py --server.port 8501 --server.address 0.0.0.0
```

### 方法 2：后台运行

```bash
nohup streamlit run app_web.py --server.port 8501 --server.address 0.0.0.0 > streamlit.log 2>&1 &
```

### 方法 3：使用 Screen/Tmux

```bash
# 创建新会话
screen -S streamlit_app

# 运行应用
streamlit run app_web.py --server.port 8501 --server.address 0.0.0.0

# 分离会话：Ctrl+A, D
# 重新连接：screen -r streamlit_app
```

## ❓ 常见问题

### Q: audiorecorder 组件无法使用？

A: 应用会自动切换到文件上传模式，你仍然可以上传音频文件进行处理。

### Q: 需要安装 ffmpeg 吗？

A: 如果你需要上传 MP3/M4A 等格式的音频，需要安装 ffmpeg：

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg
```

### Q: 如何查看历史记录？

A: 点击侧边栏的 "📅 日历" 按钮，选择日期查看该日的所有录音。

### Q: 旧版本的数据会丢失吗？

A: 不会。新版本完全兼容旧版本的数据格式，`data/` 文件夹中的所有文件都会保留。

## 📞 支持

如有问题，请检查：
1. Python 版本 >= 3.7
2. 所有依赖已正确安装：`pip list`
3. API Keys 已正确配置
4. 网络连接正常

## 🎉 开始体验

现在你可以在云服务器上运行语音识别应用了！

```bash
streamlit run app_web.py
```

享受无需物理音频设备的便利！
