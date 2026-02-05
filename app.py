"""
基于浏览器录音的Streamlit应用
适用于云服务器环境，不需要服务器端的音频设备
"""
import streamlit as st
import os
import time
import subprocess
import threading
import psutil
from datetime import datetime
from audio_processor import AudioProcessor

# 设置页面配置
st.set_page_config(
    page_title="语音识别与AI交互系统",
    page_icon="🎤",
    layout="wide"
)

# 创建音频处理器实例
if 'audio_processor' not in st.session_state:
    st.session_state.audio_processor = AudioProcessor(api_key='sk-d5d59dea2ce2448a86158ac326977694')

# 创建状态变量
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'output_content' not in st.session_state:
    st.session_state.output_content = ""
if 'ai_response' not in st.session_state:
    st.session_state.ai_response = ""
if 'system_prompt' not in st.session_state:
    # 读取system.txt内容
    if os.path.exists('system.txt'):
        with open('system.txt', 'r', encoding='utf-8') as f:
            st.session_state.system_prompt = f.read()
    else:
        st.session_state.system_prompt = "你是一个智能助手，帮助用户分析和处理输入的文本。"
if 'selected_file' not in st.session_state:
    st.session_state.selected_file = None
if 'selected_file_content' not in st.session_state:
    st.session_state.selected_file_content = ""
if 'show_calendar' not in st.session_state:
    st.session_state.show_calendar = False
if 'viewing_date' not in st.session_state:
    st.session_state.viewing_date = None
# 添加实时转录相关状态变量
if 'recording' not in st.session_state:
    st.session_state.recording = False
if 'transcription_file' not in st.session_state:
    st.session_state.transcription_file = None
if 'realtime_transcription' not in st.session_state:
    st.session_state.realtime_transcription = ""
if 'main_pid' not in st.session_state:
    st.session_state.main_pid = None
if 'main_output' not in st.session_state:
    st.session_state.main_output = ""
if 'main_error' not in st.session_state:
    st.session_state.main_error = ""

# 侧边栏配置
with st.sidebar:
    st.title("🎤 录音控制")
    
    # 使用audio_recorder组件
    try:
        from audiorecorder import audiorecorder
        
        # 开始录音按钮
        if not st.session_state.recording:
          
            
            # 尝试初始化录音组件
            try:
                audio = audiorecorder("开始录音", "停止录音", pause_prompt="暂停")
                
                if len(audio) > 0:
                    # 显示音频播放器
                    st.audio(audio.export().read(), format="audio/wav")
                    
                    # 添加处理按钮
                    if st.button("处理录音", type="primary", disabled=st.session_state.processing):
                        st.session_state.processing = True
                        
                        # 获取音频字节
                        audio_bytes = audio.export().read()
                        
                        # 显示处理中状态
                        with st.spinner("正在处理音频..."):
                            # 处理音频
                            result = st.session_state.audio_processor.process_audio_file(audio_bytes)
                            
                            if result['success']:
                                st.session_state.output_content = result['recognition_text']
                                st.session_state.ai_response = result['ai_response']
                                st.success("处理完成！")
                            else:
                                st.error(f"处理失败: {result.get('error', '未知错误')}")
                        
                        st.session_state.processing = False
                        st.rerun()
            except Exception as e:
                st.warning(f"录音组件初始化失败: {e}")
                st.info("请尝试使用文件上传模式")
        else:
            # 录音中状态
            st.info("正在录音中...")
            if st.button("停止录音", type="primary"):
                # 使用信号发送停止命令
                if 'main_pid' in st.session_state and st.session_state.main_pid:
                    import os
                    import signal
                    try:
                        # 发送SIGINT信号给main.py进程，与Ctrl+C效果相同
                        os.kill(st.session_state.main_pid, signal.SIGINT)
                        st.success("已发送停止录音信号，正在处理...")
                    except Exception as e:
                        st.error(f"发送停止信号失败: {e}")
                        # 备用方案：创建停止信号文件
                        with open('stop_recording.txt', 'w') as f:
                            f.write('stop')
                        st.warning("已使用备用方案发送停止信号")
                else:
                    # 备用方案：创建停止信号文件
                    with open('stop_recording.txt', 'w') as f:
                        f.write('stop')
                    st.warning("已使用备用方案发送停止信号")
                
                # 等待几秒钟让main.py处理停止信号
                import time
                # 增加等待时间，确保main.py有足够时间处理停止信号和保存文件
                time.sleep(3)
                
                # 检查main.py进程是否仍在运行
                if 'main_pid' in st.session_state and st.session_state.main_pid:
                    import os
                    import psutil
                    try:
                        # 检查进程是否存在
                        process = psutil.Process(st.session_state.main_pid)
                        if process.is_running():
                            # 进程仍在运行，再次发送信号
                            os.kill(st.session_state.main_pid, signal.SIGINT)
                            st.warning("进程仍在运行，已再次发送停止信号")
                            # 再等待一段时间
                            time.sleep(2)
                    except:
                        pass
                
                # 更新录音状态
                st.session_state.recording = False
                # 强制页面重新渲染，显示录音结束状态
                st.rerun()
    except ImportError:
        st.warning("audiorecorder 未安装，使用文件上传模式")
    
    # 添加实时录音按钮（与app.py类似的实现）
    if not st.session_state.recording:
        if st.button("实时录音", type="primary"):
            # 生成时间戳用于文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            # 立即设置转录文件路径
            st.session_state.transcription_file = f'data/TXT/out_{timestamp}.txt'
            
            st.session_state.recording = True
            st.session_state.output_content = ""
            st.session_state.ai_response = ""
            st.session_state.selected_file = None
            st.session_state.selected_file_content = ""
            # 添加实时转录结果状态
            st.session_state.realtime_transcription = ""
            
            # 启动录音进程
            def run_recognition():
                # 运行main.py并获取进程对象，传递时间戳作为参数
                # 使用更兼容的方式捕获输出，避免capture_output参数在旧Python版本中不可用的问题
                process = subprocess.Popen(
                    ["python", "main.py", timestamp], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    text=True
                )
                # 保存进程PID到会话状态
                st.session_state.main_pid = process.pid
                # 等待进程结束
                stdout, stderr = process.communicate()
                # 打印main.py的输出，便于调试
                print("=" * 80)
                print("main.py 标准输出:")
                print(stdout)
                print("=" * 80)
                print("main.py 标准错误:")
                print(stderr)
                print("=" * 80)
                # 将输出保存到会话状态，以便在界面上显示
                st.session_state.main_output = stdout
                st.session_state.main_error = stderr
                # 录音结束后更新状态
                st.session_state.recording = False
                # 清除PID
                if 'main_pid' in st.session_state:
                    del st.session_state.main_pid
                print("run_recognition 函数执行完成")
            
            # 在后台线程中运行
            thread = threading.Thread(target=run_recognition)
            thread.daemon = True
            thread.start()
            # 强制页面重新渲染，显示录音中状态
            st.rerun()
    
    # 始终显示文件上传选项作为备用方案
    st.divider()

    uploaded_file = st.file_uploader("选择音频文件", type=['wav', 'mp3', 'm4a'], key="audio_upload")
    
    if uploaded_file is not None:
        # 显示音频播放器
        st.audio(uploaded_file, format=f"audio/{uploaded_file.name.split('.')[-1]}")
        
        # 添加处理按钮
        if st.button("处理音频", type="primary", disabled=st.session_state.processing):
            st.session_state.processing = True
            
            # 读取音频字节
            audio_bytes = uploaded_file.read()
            
            # 显示处理中状态
            with st.spinner("正在处理音频..."):
                # 如果不是WAV格式，需要转换
                if not uploaded_file.name.endswith('.wav'):
                    try:
                        from pydub import AudioSegment
                        import io
                        
                        # 根据文件格式选择加载方式
                        file_format = uploaded_file.name.split('.')[-1]
                        audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format=file_format)
                        
                        # 转换为16kHz单声道
                        audio_segment = audio_segment.set_frame_rate(16000).set_channels(1)
                        
                        # 导出为WAV
                        wav_io = io.BytesIO()
                        audio_segment.export(wav_io, format='wav')
                        audio_bytes = wav_io.getvalue()
                    except Exception as e:
                        st.error(f"音频转换失败: {e}")
                        st.session_state.processing = False
                        st.stop()
                
                # 处理音频
                result = st.session_state.audio_processor.process_audio_file(audio_bytes)
                
                if result['success']:
                    st.session_state.output_content = result['recognition_text']
                    st.session_state.ai_response = result['ai_response']
                    st.success("处理完成！")
                else:
                    st.error(f"处理失败: {result.get('error', '未知错误')}")
            
            st.session_state.processing = False
            st.rerun()
    
    st.divider()
    
    # 添加日历按钮
    if st.button("📅 日历", key="calendar_button"):
        st.session_state.show_calendar = True
        st.session_state.viewing_date = None
        st.rerun()
    
   
    
    # 添加合并文件部分
    with st.expander("📦记录文件", expanded=True):
        # 确保必要的目录存在
        for dir_name in ['data/TXT', 'data/WAV', 'data/MD']:
            if not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)
        
        # 获取所有文件并按时间戳分组
        def get_merged_files():
            # 获取所有文件
            txt_files = [f for f in os.listdir('data/TXT') if f.endswith('.txt')]
            wav_files = [f for f in os.listdir('data/WAV') if f.endswith('.wav')]
            md_files = [f for f in os.listdir('data/MD') if f.endswith('.md')]
            
            # 提取时间戳
            def extract_timestamp(filename):
                # 从文件名中提取时间戳部分
                # 假设文件名格式为：out_20250125_110000.txt
                parts = filename.split('_')
                if len(parts) >= 3:
                    timestamp_part = f"{parts[1]}_{parts[2].split('.')[0]}"
                    return timestamp_part
                return None
            
            # 读取md文件（AI总结）内容，提取前几个字符作为标题
            def get_file_title(files):
                try:
                    # 优先使用md文件（AI总结）内容
                    if 'md' in files:
                        md_file = files['md']
                        with open(f'data/MD/{md_file}', 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                    # 如果没有md文件，使用txt文件内容
                    elif 'txt' in files:
                        txt_file = files['txt']
                        with open(f'data/TXT/{txt_file}', 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                    else:
                        return "无标题"
                    
                    # 提取标题，限制在六个字以内
                    if content:
                        # 移除换行符和多余空格
                        clean_content = ' '.join(content.split())
                        # 截取前六个字
                        title = clean_content[:6]
                        # 如果标题为空，使用默认值
                        if not title:
                            title = "无标题"
                        return title
                    return "无标题"
                except:
                    return "无标题"
            
            # 按时间戳分组
            timestamp_groups = {}
            
            # 处理txt文件
            for txt_file in txt_files:
                timestamp = extract_timestamp(txt_file)
                if timestamp:
                    if timestamp not in timestamp_groups:
                        timestamp_groups[timestamp] = {}
                    timestamp_groups[timestamp]['txt'] = txt_file

            # 处理wav文件
            for wav_file in wav_files:
                timestamp = extract_timestamp(wav_file)
                if timestamp:
                    if timestamp not in timestamp_groups:
                        timestamp_groups[timestamp] = {}
                    timestamp_groups[timestamp]['wav'] = wav_file

            # 处理md文件
            for md_file in md_files:
                timestamp = extract_timestamp(md_file)
                if timestamp:
                    if timestamp not in timestamp_groups:
                        timestamp_groups[timestamp] = {}
                    timestamp_groups[timestamp]['md'] = md_file

            # 为每个时间戳组生成标题
            for timestamp, files in timestamp_groups.items():
                # 存储文件标题（优先使用AI总结内容）
                timestamp_groups[timestamp]['title'] = get_file_title(files)
            
            # 转换为列表并排序（时间戳倒序）
            merged_files = []
            for timestamp, files in timestamp_groups.items():
                if 'txt' in files or 'wav' in files or 'md' in files:
                    merged_files.append((timestamp, files))
            
            # 按时间戳倒序排序
            merged_files.sort(key=lambda x: x[0], reverse=True)
            
            return merged_files
        
        # 获取合并文件列表
        merged_files = get_merged_files()
        
        if merged_files:
            for timestamp, files in merged_files:
                # 从txt文件中提取文件名前缀作为显示名称
                display_name = f"📦 合并文件_{timestamp}"
                if 'txt' in files:
                    txt_filename = files['txt']
                    # 提取前缀（最后两个下划线之前的部分）
                    parts = txt_filename.split('_')
                    if len(parts) >= 3:
                        # 排除最后两个部分（日期和时间）
                        file_prefix = '_'.join(parts[:-2])
                        display_name = f"📦 {file_prefix}"
                elif 'wav' in files:
                    wav_filename = files['wav']
                    parts = wav_filename.split('_')
                    if len(parts) >= 3:
                        file_prefix = '_'.join(parts[:-2])
                        display_name = f"📦 {file_prefix}"
                elif 'md' in files:
                    md_filename = files['md']
                    parts = md_filename.split('_')
                    if len(parts) >= 3:
                        file_prefix = '_'.join(parts[:-2])
                        display_name = f"📦 {file_prefix}"
                
                # 构建合并文件标识，使用与实际文件相同的前缀
                merged_file_id = f"merged_{timestamp}"
                if 'txt' in files:
                    txt_filename = files['txt']
                    parts = txt_filename.split('_')
                    if len(parts) >= 3:
                        file_prefix = '_'.join(parts[:-2])
                        merged_file_id = f"{file_prefix}_{timestamp}"
                
                if st.button(f"{display_name} ", key=f"merged_{timestamp}"):
                    # 更新状态，存储合并文件信息
                    st.session_state.selected_file = merged_file_id
                    st.session_state.selected_file_content = files
                    # 清空其他状态
                    st.session_state.output_content = ""
                    st.session_state.ai_response = ""
                    st.session_state.show_calendar = False
                    st.session_state.viewing_date = None
                    st.rerun()
        else:
            st.info("暂无合并文件")

# 主界面
if st.session_state.recording:
    # 实时转录结果显示
    st.subheader("📝 实时语音转录")
    
    # 读取并显示转录结果
    if st.session_state.transcription_file and os.path.exists(st.session_state.transcription_file):
        try:
            with open(st.session_state.transcription_file, 'r', encoding='utf-8') as f:
                content = f.read()
            if content != st.session_state.realtime_transcription:
                st.session_state.realtime_transcription = content
                print(f"更新转录结果: {content}")
        except Exception as e:
            print(f"读取转录文件时出错: {e}")
    
    # 显示转录结果
    st.text_area("转录结果", value=st.session_state.realtime_transcription, height=300)
    
    # 添加自动刷新机制
    time.sleep(0.5)  # 短暂延迟，避免刷新过快
    st.rerun()
elif st.session_state.processing:
    st.info("⏳ 正在处理音频，请稍候...")
elif st.session_state.show_calendar:
    # 日历界面（复用原有代码）
    st.header("📅 日历")
    
    # 获取所有文件的日期和数量
    def get_file_stats():
        date_stats = {}
        # 检查TXT文件
        if os.path.exists('data/TXT'):
            for file in os.listdir('data/TXT'):
                if file.endswith('.txt'):
                    try:
                        parts = file.split('_')
                        for part in parts:
                            if len(part) == 8 and part.isdigit():
                                date_str = part
                                if date_str not in date_stats:
                                    date_stats[date_str] = 0
                                date_stats[date_str] += 1
                                break
                    except:
                        pass
        return date_stats
    
    file_stats = get_file_stats()
    
    # 生成月历
    import datetime
    
    # 获取当前日期或选中的月份
    if 'current_month' not in st.session_state:
        st.session_state.current_month = datetime.datetime.now()
    
    # 月份导航
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("← 上个月", key="prev_month", use_container_width=True):
            st.session_state.current_month = st.session_state.current_month.replace(day=1) - datetime.timedelta(days=1)
            st.rerun()
    with col2:
        st.subheader(f"{st.session_state.current_month.year}年{st.session_state.current_month.month}月")
    with col3:
        if st.button("下个月 →", key="next_month", use_container_width=True):
            if st.session_state.current_month.month == 12:
                next_month = st.session_state.current_month.replace(year=st.session_state.current_month.year + 1, month=1, day=1)
            else:
                next_month = st.session_state.current_month.replace(month=st.session_state.current_month.month + 1, day=1)
            st.session_state.current_month = next_month
            st.rerun()
    
    # 生成月份的日历
    year = st.session_state.current_month.year
    month = st.session_state.current_month.month
    
    # 获取月份第一天是星期几
    first_day = datetime.datetime(year, month, 1)
    first_day_weekday = first_day.weekday()
    
    # 获取月份的天数
    if month == 12:
        last_day = datetime.datetime(year + 1, 1, 1) - datetime.timedelta(days=1)
    else:
        last_day = datetime.datetime(year, month + 1, 1) - datetime.timedelta(days=1)
    days_in_month = last_day.day
    
    # 创建日历网格
    st.write("")
    
    # 星期标题
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    cols = st.columns(7)
    for i, day in enumerate(weekdays):
        cols[i].markdown(f"**{day}**")
    
    # 填充日历
    day_num = 1
    week_num = 0
    
    while day_num <= days_in_month:
        cols = st.columns(7)
        
        # 填充第一周的空白
        if week_num == 0:
            for i in range(first_day_weekday):
                cols[i].write("")
        
        # 填充日期
        start_col = first_day_weekday if week_num == 0 else 0
        for i in range(start_col, 7):
            if day_num > days_in_month:
                break
            
            # 构建日期字符串
            date_str = f"{year}{month:02d}{day_num:02d}"
            
            # 获取当天的文件数量
            file_count = file_stats.get(date_str, 0)
            
            # 日期按钮
            button_label = f"{day_num}"
            if file_count > 0:
                button_label += f"({file_count}次)"
            
            if cols[i].button(button_label, key=f"cal_{date_str}", use_container_width=True, type="primary" if file_count > 0 else "secondary"):
                st.session_state.viewing_date = date_str
                st.session_state.show_calendar = False
                st.rerun()
            
            day_num += 1
        week_num += 1
    
    # 返回按钮
    if st.button("返回主界面", key="back_from_calendar", use_container_width=True):
        st.session_state.show_calendar = False
        st.rerun()

elif st.session_state.viewing_date:
    # 显示特定日期的文件
    viewing_date = st.session_state.viewing_date
    year = viewing_date[:4]
    month = viewing_date[4:6]
    day = viewing_date[6:8]
    
    st.header(f"📁 {year}年{month}月{day}日的文件")
    
    # 返回日历按钮
    if st.button("返回日历", key="back_to_calendar", type="secondary"):
        st.session_state.viewing_date = None
        st.session_state.show_calendar = True
        st.rerun()
    
    # 获取选中日期的文件
    def get_files_by_date(date_str):
        txt_files = []
        wav_files = []
        md_files = []
        
        if os.path.exists('data/TXT'):
            for file in os.listdir('data/TXT'):
                if file.endswith('.txt') and date_str in file:
                    txt_files.append(file)
        
        if os.path.exists('data/WAV'):
            for file in os.listdir('data/WAV'):
                if file.endswith('.wav') and date_str in file:
                    wav_files.append(file)
        
        if os.path.exists('data/MD'):
            for file in os.listdir('data/MD'):
                if file.endswith('.md') and date_str in file:
                    md_files.append(file)
        
        return txt_files, wav_files, md_files
    
    txt_files, wav_files, md_files = get_files_by_date(viewing_date)
    
    # 显示文件
    if txt_files or wav_files or md_files:
        if txt_files:
            st.subheader("📝 语音识别文件")
            for file in txt_files:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{file}**")
                with col2:
                    if st.button("查看", key=f"view_txt_{file}", type="primary", use_container_width=True):
                        with open(f'data/TXT/{file}', 'r', encoding='utf-8') as f:
                            content = f.read()
                        st.session_state.selected_file = file
                        st.session_state.selected_file_content = content
                        st.session_state.viewing_date = None
                        st.rerun()
        
        if wav_files:
            st.subheader("🎵 音频文件")
            for file in wav_files:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{file}**")
                with col2:
                    if st.button("查看", key=f"view_wav_{file}", type="primary", use_container_width=True):
                        with open(f'data/WAV/{file}', 'rb') as f:
                            audio_content = f.read()
                        st.session_state.selected_file = file
                        st.session_state.selected_file_content = audio_content
                        st.session_state.viewing_date = None
                        st.rerun()
        
        if md_files:
            st.subheader("🤖 AI总结文件")
            for file in md_files:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{file}**")
                with col2:
                    if st.button("查看", key=f"view_md_{file}", type="primary", use_container_width=True):
                        with open(f'data/MD/{file}', 'r', encoding='utf-8') as f:
                            content = f.read()
                        st.session_state.selected_file = file
                        st.session_state.selected_file_content = content
                        st.session_state.viewing_date = None
                        st.rerun()
    else:
        st.info("该日期暂无文件")

elif st.session_state.selected_file:
    # 显示选中的文件内容
    # 检查是否为合并文件（通过检查 selected_file_content 是否为字典且包含文件类型键）
    if isinstance(st.session_state.selected_file_content, dict) and ('txt' in st.session_state.selected_file_content or 'wav' in st.session_state.selected_file_content or 'md' in st.session_state.selected_file_content):
        # 处理合并文件
        merged_files = st.session_state.selected_file_content
        title = merged_files.get('title', st.session_state.selected_file)
        st.header(f"📦 {title}")
        
        # 获取合并的文件信息
        
        # 依次显示音频文件、txt文件、md文件
        # 1. 显示音频文件
        if 'wav' in merged_files:
            st.subheader("🎵 音频文件")
            wav_file = merged_files['wav']
            try:
                with open(f'data/WAV/{wav_file}', 'rb') as f:
                    audio_content = f.read()
                st.audio(audio_content, format="audio/wav")
                
                # 添加下载按钮
                st.download_button(
                    label=f"下载音频 {wav_file}",
                    data=audio_content,
                    file_name=wav_file,
                    mime="audio/wav"
                )
            except Exception as e:
                st.error(f"无法加载音频文件: {e}")
        
        # 2. 显示txt文件
        if 'txt' in merged_files:
            st.subheader("📝 文本文件")
            txt_file = merged_files['txt']
            try:
                with open(f'data/TXT/{txt_file}', 'r', encoding='utf-8') as f:
                    txt_content = f.read()
                st.text_area("文件内容", txt_content, height=300)
                
                # 添加下载按钮
                st.download_button(
                    label=f"下载文本 {txt_file}",
                    data=txt_content,
                    file_name=txt_file,
                    mime="text/plain"
                )
            except Exception as e:
                st.error(f"无法加载文本文件: {e}")
        
        # 3. 显示md文件
        if 'md' in merged_files:
            st.subheader("🤖 AI分析文件")
            md_file = merged_files['md']
            try:
                with open(f'data/MD/{md_file}', 'r', encoding='utf-8') as f:
                    md_content = f.read()
                st.markdown(md_content)
                
                # 添加下载按钮
                st.download_button(
                    label=f"下载AI分析 {md_file}",
                    data=md_content,
                    file_name=md_file,
                    mime="text/markdown"
                )
            except Exception as e:
                st.error(f"无法加载AI分析文件: {e}")
    else:
        # 处理单个文件
        st.header(f"📝 {st.session_state.selected_file}")
        
        # 根据文件类型显示内容
        if st.session_state.selected_file.endswith('.md'):
            st.markdown(st.session_state.selected_file_content)
            mime_type = "text/markdown"
        elif st.session_state.selected_file.endswith('.wav'):
            st.audio(st.session_state.selected_file_content, format="audio/wav")
            mime_type = "audio/wav"
        else:
            st.text_area("文件内容", st.session_state.selected_file_content, height=400)
            mime_type = "text/plain"
        
        # 添加下载按钮
        st.download_button(
            label=f"下载 {st.session_state.selected_file}",
            data=st.session_state.selected_file_content,
            file_name=st.session_state.selected_file,
            mime=mime_type
        )
    
    # 添加返回按钮
    if st.button("返回主界面"):
        st.session_state.selected_file = None
        st.session_state.selected_file_content = ""
        st.rerun()

elif st.session_state.output_content or st.session_state.ai_response:
    # 显示处理结果
    st.header("📊 处理结果")
    
    if st.session_state.output_content:
        st.subheader("📝 语音识别结果")
        st.text_area("识别文本", st.session_state.output_content, height=200)
    
    if st.session_state.ai_response:
        st.subheader("🤖 AI分析结果")
        st.markdown(st.session_state.ai_response)
    
    # 添加返回按钮
    if st.button("返回主界面"):
        st.session_state.output_content = ""
        st.session_state.ai_response = ""
        st.rerun()

else:
    # 主界面
    st.header("🎤 语音识别与AI交互系统")
    st.info("请在侧边栏开始录音或上传音频文件")
    
    # 显示系统功能介绍
    st.markdown("""
    ### 🌟 系统功能
    - **浏览器录音**：直接在浏览器中录音，无需服务器音频设备
    - **文件上传**：支持上传 WAV、MP3、M4A 等格式的音频文件
    - **语音识别**：将音频转换为文本
    - **AI 分析**：对识别的文本进行智能分析
    - **文件管理**：保存和管理所有录音和分析结果
    - **历史记录**：通过日历查看历史文件

    ### 📋 使用流程
    1. 在侧边栏选择录音或上传音频文件
    2. 对于录音：点击"开始录音"→说话→点击"停止录音"→点击"处理录音"
    3. 对于上传：选择音频文件→点击"处理音频"
    4. 系统自动进行语音识别和AI分析
    5. 查看处理结果
    6. 在侧边栏管理和查看历史文件
    
    ### ☁️ 云服务器优化
    - ✅ 不依赖服务器音频设备（无需麦克风）
    - ✅ 所有音频在浏览器端捕获
    - ✅ 支持多种音频格式
    - ✅ 适用于各种云部署环境
    """)
