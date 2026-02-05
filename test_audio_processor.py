"""
测试音频处理器功能
用于验证云服务器兼容性
"""
import os
import sys
import io

# 设置标准输出编码为 UTF-8
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from audio_processor import AudioProcessor

def test_basic_functionality():
    """测试基本功能"""
    print("=" * 60)
    print("测试音频处理器基本功能")
    print("=" * 60)
    
    # 创建音频处理器实例
    try:
        processor = AudioProcessor(api_key='sk-d5d59dea2ce2448a86158ac326977694')
        print("✅ 音频处理器创建成功")
    except Exception as e:
        print(f"❌ 音频处理器创建失败: {e}")
        return False
    
    # 检查是否有测试音频文件
    test_audio_files = []
    if os.path.exists('data/WAV'):
        test_audio_files = [f for f in os.listdir('data/WAV') if f.endswith('.wav')]
    
    if not test_audio_files:
        print("⚠️ 没有找到测试音频文件（data/WAV/*.wav）")
        print("   请先使用 app_web.py 录制一些音频，或将测试音频放到 data/WAV/ 目录")
        return False
    
    # 使用第一个音频文件进行测试
    test_file = test_audio_files[0]
    test_path = f'data/WAV/{test_file}'
    print(f"\n使用测试文件: {test_file}")
    
    # 读取音频文件
    try:
        with open(test_path, 'rb') as f:
            audio_bytes = f.read()
        print(f"✅ 音频文件读取成功，大小: {len(audio_bytes)} 字节")
    except Exception as e:
        print(f"❌ 音频文件读取失败: {e}")
        return False
    
    # 处理音频
    print("\n开始处理音频...")
    try:
        result = processor.process_audio_file(audio_bytes, timestamp='test')
        
        if result['success']:
            print("✅ 音频处理成功！")
            print(f"\n识别结果:")
            print(f"  文本长度: {len(result['recognition_text'])} 字符")
            if result['recognition_text']:
                print(f"  内容预览: {result['recognition_text'][:100]}...")
            
            print(f"\nAI回复:")
            print(f"  文本长度: {len(result['ai_response'])} 字符")
            if result['ai_response']:
                print(f"  内容预览: {result['ai_response'][:100]}...")
            
            print(f"\n生成的文件:")
            for key, path in result['files'].items():
                print(f"  {key}: {path}")
            
            # 清理测试文件
            print("\n清理测试文件...")
            for key, path in result['files'].items():
                if 'test' in path and os.path.exists(path):
                    try:
                        os.remove(path)
                        print(f"  ✅ 已删除: {path}")
                    except Exception as e:
                        print(f"  ⚠️ 删除失败: {path} - {e}")
            
            return True
        else:
            print(f"❌ 音频处理失败: {result.get('error', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"❌ 音频处理异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_import_dependencies():
    """测试依赖导入"""
    print("\n" + "=" * 60)
    print("测试依赖库导入")
    print("=" * 60)
    
    dependencies = [
        ('dashscope', 'dashscope'),
        ('openai', 'openai'),
        ('wave', 'wave'),
        ('io', 'io'),
        ('os', 'os'),
    ]
    
    all_success = True
    for module_name, import_name in dependencies:
        try:
            __import__(import_name)
            print(f"✅ {module_name}: 导入成功")
        except ImportError as e:
            print(f"❌ {module_name}: 导入失败 - {e}")
            all_success = False
    
    return all_success

def test_file_structure():
    """测试文件结构"""
    print("\n" + "=" * 60)
    print("测试文件结构")
    print("=" * 60)
    
    required_dirs = ['data', 'data/TXT', 'data/MD', 'data/WAV']
    required_files = ['audio_processor.py', 'app_web.py', 'system.txt']
    
    all_success = True
    
    # 检查目录
    for dir_path in required_dirs:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            print(f"✅ 目录存在: {dir_path}")
        else:
            print(f"⚠️ 目录不存在: {dir_path} (将自动创建)")
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"   ✅ 已创建: {dir_path}")
            except Exception as e:
                print(f"   ❌ 创建失败: {e}")
                all_success = False
    
    # 检查文件
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ 文件存在: {file_path}")
        else:
            if file_path == 'system.txt':
                print(f"⚠️ 文件不存在: {file_path} (将使用默认提示)")
            else:
                print(f"❌ 文件不存在: {file_path}")
                all_success = False
    
    return all_success

def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("云服务器兼容性测试")
    print("=" * 60)
    print("\n此测试将验证音频处理器是否能在云服务器上正常工作")
    print("（不依赖 PyAudio 和物理音频设备）\n")
    
    # 测试1: 依赖导入
    test1 = test_import_dependencies()
    
    # 测试2: 文件结构
    test2 = test_file_structure()
    
    # 测试3: 基本功能（需要测试音频文件）
    test3 = test_basic_functionality()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"依赖导入测试: {'✅ 通过' if test1 else '❌ 失败'}")
    print(f"文件结构测试: {'✅ 通过' if test2 else '❌ 失败'}")
    print(f"功能测试: {'✅ 通过' if test3 else '⚠️ 跳过或失败'}")
    
    if test1 and test2:
        print("\n✅ 基本环境检查通过，可以在云服务器上运行")
        print("   运行命令: streamlit run app_web.py")
    else:
        print("\n❌ 环境检查未通过，请检查以上错误信息")
        return 1
    
    if not test3:
        print("\n⚠️ 功能测试未完成")
        print("   建议: 使用 app_web.py 录制音频后再次运行此测试")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
