"""
基于浏览器录音的Streamlit应用
适用于云服务器环境，不需要服务器端的音频设备
"""
import streamlit as st
import os
import time
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

# 侧边栏配置
with st.sidebar:
    st.title("🎤 录音控制")
    
    # 使用audio_recorder组件
    try:
        from audiorecorder import audiorecorder
        
        st.info("点击下方按钮开始/停止录音")
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
    except ImportError:
        st.warning("audiorecorder 未安装，使用文件上传模式")
        
        # 备用方案：文件上传
        st.info("请上传音频文件（WAV格式，16kHz，单声道）")
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
    
    st.divider()
    
    # 显示文件列表 - 使用expander实现折叠展开
    with st.expander("📝 语音识别文件", expanded=True):
        # 确保data/TXT文件夹存在
        if not os.path.exists('data/TXT'):
            os.makedirs('data/TXT', exist_ok=True)
        # 获取所有.txt文件
        out_files = [f for f in os.listdir('data/TXT') if f.endswith('.txt')]
        # 按文件名排序（时间戳倒序）
        out_files.sort(reverse=True)
        
        if out_files:
            for file in out_files:
                if st.button(f"{file}", key=f"out_{file}"):
                    # 读取文件内容
                    with open(f'data/TXT/{file}', 'r', encoding='utf-8') as f:
                        content = f.read()
                    # 更新状态
                    st.session_state.selected_file = file
                    st.session_state.selected_file_content = content
                    # 清空其他状态
                    st.session_state.output_content = ""
                    st.session_state.ai_response = ""
                    st.session_state.show_calendar = False
                    st.session_state.viewing_date = None
                    st.rerun()
        else:
            st.info("暂无语音识别文件")

    with st.expander("🎵 音频文件", expanded=True):
        # 确保data/WAV文件夹存在
        if not os.path.exists('data/WAV'):
            os.makedirs('data/WAV', exist_ok=True)
        # 获取所有.wav文件
        audio_files = [f for f in os.listdir('data/WAV') if f.endswith('.wav')]
        # 按文件名排序（时间戳倒序）
        audio_files.sort(reverse=True)
        
        if audio_files:
            for file in audio_files:
                if st.button(f"{file}", key=f"audio_{file}"):
                    # 读取文件内容
                    with open(f'data/WAV/{file}', 'rb') as f:
                        audio_content = f.read()
                    # 更新状态
                    st.session_state.selected_file = file
                    st.session_state.selected_file_content = audio_content
                    # 清空其他状态
                    st.session_state.output_content = ""
                    st.session_state.ai_response = ""
                    st.session_state.show_calendar = False
                    st.session_state.viewing_date = None
                    st.rerun()
        else:
            st.info("暂无音频文件")

    with st.expander("🤖 AI总结文件", expanded=True):
        # 确保data/MD文件夹存在
        if not os.path.exists('data/MD'):
            os.makedirs('data/MD', exist_ok=True)
        # 获取所有.md文件
        cord_files = [f for f in os.listdir('data/MD') if f.endswith('.md')]
        # 按文件名排序（时间戳倒序）
        cord_files.sort(reverse=True)
        
        if cord_files:
            for file in cord_files:
                if st.button(f"{file}", key=f"cord_{file}"):
                    # 读取文件内容
                    with open(f'data/MD/{file}', 'r', encoding='utf-8') as f:
                        content = f.read()
                    # 更新状态
                    st.session_state.selected_file = file
                    st.session_state.selected_file_content = content
                    # 清空其他状态
                    st.session_state.output_content = ""
                    st.session_state.ai_response = ""
                    st.session_state.show_calendar = False
                    st.session_state.viewing_date = None
                    st.rerun()
        else:
            st.info("暂无AI回复文件")

# 主界面
if st.session_state.processing:
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
