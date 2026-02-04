"""
音频处理模块 - 处理从浏览器上传的音频并进行语音识别
不依赖PyAudio，适用于云服务器环境
"""
import os
import time
from datetime import datetime
import dashscope
from dashscope.audio.asr import *
import wave
import io

class AudioProcessor:
    def __init__(self, api_key):
        """初始化音频处理器"""
        dashscope.api_key = api_key
        dashscope.base_websocket_api_url = 'wss://dashscope.aliyuncs.com/api-ws/v1/inference'
        self.sample_rate = 16000
        self.channels = 1
        
    def process_audio_file(self, audio_bytes, timestamp=None):
        """
        处理音频文件（从浏览器上传的音频）
        
        Args:
            audio_bytes: 音频文件的字节数据
            timestamp: 时间戳（可选）
            
        Returns:
            dict: 包含识别结果、AI回复和文件路径
        """
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 创建文件路径
        temp_output_file_path = f'data/TXT/out_{timestamp}.txt'
        temp_cord_file_path = f'data/MD/cord_{timestamp}.md'
        temp_audio_file_path = f'data/WAV/audio_{timestamp}.wav'
        
        # 确保目录存在
        os.makedirs('data/TXT', exist_ok=True)
        os.makedirs('data/MD', exist_ok=True)
        os.makedirs('data/WAV', exist_ok=True)
        
        try:
            # 保存原始音频文件
            with open(temp_audio_file_path, 'wb') as f:
                f.write(audio_bytes)
            print(f"音频文件已保存: {temp_audio_file_path}")
            
            # 读取音频文件进行识别
            recognition_result = self._recognize_audio_file(temp_audio_file_path, temp_output_file_path)
            
            # 读取识别结果
            recognition_text = ""
            if os.path.exists(temp_output_file_path):
                with open(temp_output_file_path, 'r', encoding='utf-8') as f:
                    recognition_text = f.read()
            
            # 如果有识别结果，进行AI分析
            ai_response = ""
            if recognition_text:
                ai_response = self._generate_ai_response(recognition_text, temp_cord_file_path)
            else:
                # 创建空的AI回复文件
                with open(temp_cord_file_path, 'w', encoding='utf-8') as f:
                    f.write("没有识别到文本内容")
            
            # 根据内容生成文件名
            if recognition_text and len(recognition_text.strip()) > 0:
                final_paths = self._rename_files_with_ai(
                    recognition_text, 
                    timestamp,
                    temp_output_file_path,
                    temp_cord_file_path,
                    temp_audio_file_path
                )
            else:
                final_paths = {
                    'txt': temp_output_file_path,
                    'md': temp_cord_file_path,
                    'wav': temp_audio_file_path
                }
            
            return {
                'success': True,
                'recognition_text': recognition_text,
                'ai_response': ai_response,
                'files': final_paths
            }
            
        except Exception as e:
            print(f"处理音频时出错: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _recognize_audio_file(self, audio_file_path, output_file_path):
        """使用文件识别API识别音频"""
        try:
            # 使用阿里云的文件识别API
            from dashscope.audio.asr import Recognition
            
            # 读取音频数据
            with open(audio_file_path, 'rb') as f:
                audio_data = f.read()
            
            # 创建识别回调
            recognition_results = []
            
            class FileCallback(RecognitionCallback):
                def on_open(self):
                    print('识别连接已打开')
                
                def on_close(self):
                    print('识别连接已关闭')
                
                def on_complete(self):
                    print('识别完成')
                
                def on_error(self, message):
                    print(f'识别错误: {message.message}')
                
                def on_event(self, result):
                    sentence = result.get_sentence()
                    if 'text' in sentence:
                        text = sentence['text']
                        print(f'识别结果: {text}')
                        if RecognitionResult.is_sentence_end(sentence):
                            recognition_results.append(text)
            
            callback = FileCallback()
            
            # 创建识别实例
            recognition = Recognition(
                model='fun-asr-realtime',
                format='pcm',
                sample_rate=16000,
                semantic_punctuation_enabled=False,
                callback=callback
            )
            
            # 启动识别
            recognition.start()
            
            # 读取音频文件并分块发送
            chunk_size = 3200 * 2  # 每次发送3200个采样点，16位=2字节
            
            # 如果是WAV文件，跳过文件头
            audio_io = io.BytesIO(audio_data)
            try:
                wf = wave.open(audio_io, 'rb')
                # 验证音频格式
                if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
                    print(f"音频格式不匹配: channels={wf.getnchannels()}, sampwidth={wf.getsampwidth()}, rate={wf.getframerate()}")
                    # 尝试转换（这里只是读取数据，实际转换需要额外的库）
                raw_data = wf.readframes(wf.getnframes())
                wf.close()
            except:
                # 如果不是WAV格式，直接使用原始数据
                raw_data = audio_data
            
            # 分块发送音频数据
            offset = 0
            while offset < len(raw_data):
                chunk = raw_data[offset:offset+chunk_size]
                recognition.send_audio_frame(chunk)
                offset += chunk_size
                time.sleep(0.01)  # 短暂延迟，模拟实时流
            
            # 停止识别
            recognition.stop()
            
            # 保存识别结果
            if recognition_results:
                with open(output_file_path, 'w', encoding='utf-8') as f:
                    for text in recognition_results:
                        f.write(text + '\n')
                print(f'识别结果已保存: {output_file_path}')
            
            return True
            
        except Exception as e:
            print(f"音频识别出错: {e}")
            # 创建空的识别结果文件
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write("")
            return False
    
    def _generate_ai_response(self, text, output_file_path):
        """生成AI回复"""
        try:
            from openai import OpenAI
            
            # 读取system提示
            system_content = "你是一个智能助手，帮助用户分析和处理输入的文本。"
            if os.path.exists('system.txt'):
                with open('system.txt', 'r', encoding='utf-8') as f:
                    system_content = f.read()
            
            # 创建DeepSeek客户端
            client = OpenAI(
                api_key="sk-c0e2db4baac34732b5fe022aca40961d",
                base_url="https://api.deepseek.com"
            )
            
            # 调用API
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": text}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            ai_response = response.choices[0].message.content
            
            # 保存AI回复
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write(ai_response)
            
            print(f'AI回复已保存: {output_file_path}')
            return ai_response
            
        except Exception as e:
            print(f"生成AI回复时出错: {e}")
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write(f"AI分析失败: {str(e)}")
            return f"AI分析失败: {str(e)}"
    
    def _rename_files_with_ai(self, text, timestamp, txt_path, md_path, wav_path):
        """使用AI生成文件名关键词并重命名文件"""
        try:
            from openai import OpenAI
            
            # 构建文件名生成提示
            filename_prompt = f"请分析以下文本内容，提取最能概括内容的简短关键词（1-3个词），用于作为文件名。\n\n文本内容：{text}\n\n要求：\n1. 关键词必须简洁明了\n2. 不要包含特殊字符\n3. 用中文回答\n4. 直接返回关键词，不要有其他说明"
            
            # 创建客户端
            client = OpenAI(
                api_key="sk-c0e2db4baac34732b5fe022aca40961d",
                base_url="https://api.deepseek.com"
            )
            
            # 调用API生成文件名
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个文件名生成助手，根据文本内容提取简洁的关键词作为文件名"},
                    {"role": "user", "content": filename_prompt}
                ],
                temperature=0.5,
                max_tokens=50
            )
            
            # 提取文件名关键词
            filename_keyword = response.choices[0].message.content.strip()
            # 清理文件名
            filename_keyword = ''.join(c for c in filename_keyword if c.isalnum() or c == '_' or c == '-' or c == ' ')
            filename_keyword = filename_keyword.replace(' ', '_')
            filename_keyword = filename_keyword[:50]
            
            print(f'生成的文件名关键词: {filename_keyword}')
            
            # 生成最终文件路径
            final_txt = f'data/TXT/{filename_keyword}_{timestamp}.txt'
            final_md = f'data/MD/{filename_keyword}_{timestamp}.md'
            final_wav = f'data/WAV/{filename_keyword}_{timestamp}.wav'
            
            # 重命名文件
            if os.path.exists(txt_path):
                os.rename(txt_path, final_txt)
                print(f'TXT文件已重命名: {final_txt}')
            
            if os.path.exists(md_path):
                os.rename(md_path, final_md)
                print(f'MD文件已重命名: {final_md}')
            
            if os.path.exists(wav_path):
                os.rename(wav_path, final_wav)
                print(f'WAV文件已重命名: {final_wav}')
            
            return {
                'txt': final_txt,
                'md': final_md,
                'wav': final_wav
            }
            
        except Exception as e:
            print(f"重命名文件时出错: {e}")
            return {
                'txt': txt_path,
                'md': md_path,
                'wav': wav_path
            }
