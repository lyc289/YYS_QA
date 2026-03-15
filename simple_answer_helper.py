"""
阴阳师答题助手 - 完整版
使用adb直接截图，确保每次都是实时截图
"""

import os
import sys
import subprocess
import time
import json
from PIL import Image

# 添加项目路径
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)


class EnhancedAnswerHelper:
    """增强版答题助手 - 移除测试模式，直接使用adb"""

    def __init__(self, device_id=None, adb_path=None, config_path=None):
        """
        初始化助手

        Args:
            device_id: 设备ID，None则使用config.json配置或自动检测
            adb_path: adb完整路径，None则使用config.json配置
            config_path: 配置文件路径，默认为项目目录下的config.json
        """
        self.project_dir = project_dir

        # 加载配置文件
        self.config = self._load_config(config_path)

        # 获取adb_path（参数 > config > 默认值）
        if adb_path is None:
            adb_path = self.config.get('adb_path')
            if not adb_path:
                # 尝试常见的adb路径
                common_paths = [
                    r"D:\leidian\LDPlayer9\adb.exe",
                    r"D:\leidian\LDPlayer4\adb.exe",
                    r"C:\Program Files\Nox\bin\adb.exe",
                    r"C:\Program Files\BlueStacks_nxt\HD-Adb.exe",
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        adb_path = path
                        break

        self.adb_path = adb_path
        self.device_id = device_id or self.config.get('device_id')

        # 创建img文件夹
        self.img_dir = os.path.join(self.project_dir, "img")
        os.makedirs(self.img_dir, exist_ok=True)

        # 自动检测设备
        if self.device_id is None:
            self.device_id = self._auto_detect_device()

        # 验证adb和设备
        self._validate_connection()

        print(f"[OK] 使用设备: {self.device_id}")
        print(f"[OK] adb路径: {self.adb_path}")
        print(f"[OK] 图片保存目录: {self.img_dir}")

    def _load_config(self, config_path=None):
        """加载配置文件"""
        if config_path is None:
            config_path = os.path.join(self.project_dir, "config.json")

        default_config = {
            "adb_path": None,
            "device_id": None,
            "question_region": {"x1": 100, "y1": 200, "x2": 500, "y2": 600},
            "ocr_settings": {"engine": "easyocr"},
            "search_settings": {"top_k": 10}
        }

        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    import json
                    config = json.load(f)
                print(f"[OK] 加载配置: {config_path}")
                return {**default_config, **config}
            else:
                print(f"[INFO] 配置文件不存在，使用默认配置")
                return default_config
        except Exception as e:
            print(f"[INFO] 加载配置失败: {e}，使用默认配置")
            return default_config

    def _get_connected_devices(self):
        """获取已连接的设备列表"""
        try:
            result = subprocess.run(
                f'"{self.adb_path}" devices',
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )

            lines = result.stdout.strip().split('\n')
            devices = []
            for line in lines[1:]:  # 跳过第一行标题
                if '\tdevice' in line:
                    device_id = line.split('\t')[0]
                    devices.append(device_id)

            return devices

        except Exception as e:
            print(f"[X] 检测设备失败: {e}")
            return []

    def _auto_detect_device(self):
        """自动检测连接的设备"""
        print("\n[检测设备]")

        devices = self._get_connected_devices()

        if not devices:
            print("[X] 未检测到设备")
            print("\n请确保：")
            print("1. 模拟器已启动")
            print("2. 运行以下命令检查：")
            print(f'   "{self.adb_path}" devices')
            raise SystemExit(1)

        if len(devices) > 1:
            print(f"[OK] 检测到{len(devices)}个设备，使用第一个: {devices[0]}")
            return devices[0]

        print(f"[OK] 检测到设备: {devices[0]}")
        return devices[0]

    def _validate_connection(self):
        """验证adb和设备连接"""
        try:
            # 测试adb命令
            result = subprocess.run(
                f'"{self.adb_path}" -s {self.device_id} shell echo test',
                shell=True,
                capture_output=True,
                timeout=5
            )

            if result.returncode == 0:
                print(f"[OK] adb连接正常")
                return True
            else:
                print(f"[X] adb连接失败: {result.stderr.decode()}")
                return False

        except Exception as e:
            print(f"[X] 验证连接失败: {e}")
            return False

    def capture_screen(self, output_path=None):
        """
        使用adb截取屏幕（每次都重新截图）

        Args:
            output_path: 输出文件路径，None则使用默认路径

        Returns:
            str: 截图文件路径，失败返回None
        """
        import time

        if output_path is None:
            # 使用时间戳确保每次都是新文件，保存到img文件夹
            timestamp = time.strftime("%H%M%S")
            output_path = os.path.join(self.img_dir, f"temp_screen_{timestamp}.png")

        print(f"-> 截取屏幕到: {output_path}")

        # 删除旧文件（如果存在）
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
                print(f"  删除旧文件")
            except:
                pass

        try:
            # 方法1: 直接截取到本地
            print("  方法1: 直接截图...")
            cmd = f'"{self.adb_path}" -s {self.device_id} shell screencap -p'
            print(f"  执行命令: {cmd}")

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                timeout=30
            )

            print(f"  返回码: {result.returncode}")

            if result.returncode == 0:
                # 保存截图（Windows下需要转换\r\n）
                content = result.stdout.replace(b'\r\n', b'\n')
                with open(output_path, 'wb') as f:
                    f.write(content)

                if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
                    file_time = os.path.getmtime(output_path)
                    current_time = time.time()

                    img = Image.open(output_path)
                    print(f"  [OK] 截图成功")
                    print(f"  文件: {os.path.basename(output_path)}")
                    print(f"  尺寸: {img.size}")
                    print(f"  大小: {os.path.getsize(output_path)} 字节")
                    print(f"  时间: {time.strftime('%H:%M:%S', time.localtime(file_time))}")
                    print(f"  延迟: {current_time - file_time:.1f}秒前")
                    return output_path
                else:
                    print(f"  [X] 截图文件太小或无效")

            else:
                print(f"  [X] adb截图失败")
                if result.stderr:
                    print(f"  错误: {result.stderr.decode()[:200]}")

            # 方法2: 先保存到设备再拉取
            print("  方法2: 设备中转...")
            remote_path = "/sdcard/temp_screen.png"

            # 截图到设备
            cmd = f'"{self.adb_path}" -s {self.device_id} shell screencap -p {remote_path}'
            print(f"  执行命令: {cmd}")

            result = subprocess.run(cmd, shell=True, timeout=30)

            if result.returncode == 0:
                # 拉取到本地
                cmd = f'"{self.adb_path}" -s {self.device_id} pull {remote_path} "{output_path}"'
                print(f"  执行命令: {cmd}")

                result = subprocess.run(cmd, shell=True, capture_output=True, timeout=30)

                if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
                    print(f"  [OK] 方法2成功")
                    # 清理设备上的临时文件
                    subprocess.run(
                        f'"{self.adb_path}" -s {self.device_id} shell rm {remote_path}',
                        shell=True
                    )
                    return output_path
                else:
                    print(f"  [X] 方法2拉取失败")
            else:
                print(f"  [X] 方法2失败")

            print(f"  [X] 所有方法都失败了")
            return None

        except subprocess.TimeoutExpired:
            print("  [X] 截图超时")
            return None
        except Exception as e:
            print(f"  [X] 截图失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def crop_region(self, input_path, region, output_path=None):
        """
        裁剪图片区域

        Args:
            input_path: 输入图片路径
            region: (x1, y1, x2, y2) 区域坐标
            output_path: 输出路径，None则使用默认路径

        Returns:
            str: 裁剪后的图片路径，失败返回None
        """
        if output_path is None:
            output_path = os.path.join(self.img_dir, "temp_question.png")

        print(f"-> 裁剪区域: {region}")

        try:
            # 打开图片
            img = Image.open(input_path)
            print(f"  原图尺寸: {img.size}")

            # 调整坐标（防止超出范围）
            x1, y1, x2, y2 = region
            width, height = img.size

            x1 = max(0, min(x1, width))
            y1 = max(0, min(y1, height))
            x2 = max(0, min(x2, width))
            y2 = max(0, min(y2, height))

            if x1 >= x2 or y1 >= y2:
                print(f"  [X] 坐标无效: ({x1},{y1}) -> ({x2},{y2})")
                return None

            # 裁剪
            cropped = img.crop((x1, y1, x2, y2))
            print(f"  裁剪尺寸: {cropped.size}")

            # 保存
            cropped.save(output_path)
            print(f"  [OK] 裁剪成功: {output_path}")

            return output_path

        except Exception as e:
            print(f"  [X] 裁剪失败: {e}")
            return None

    def ocr_recognize(self, image_path):
        """
        OCR识别图片中的文字

        Args:
            image_path: 图片路径

        Returns:
            str: 识别出的文字
        """
        print(f"-> OCR识别: {os.path.basename(image_path)}")

        try:
            from ocr import recognize_text

            text = recognize_text(image_path)

            if text:
                print(f"  [OK] 识别文字: {text}")
            else:
                print(f"  [X] 未识别到文字")

            return text

        except ImportError:
            print("  [X] OCR模块未安装")
            print("  请运行: pip install easyocr")
            return ""
        except Exception as e:
            print(f"  [X] OCR失败: {e}")
            return ""

    def search_answer(self, query):
        """
        搜索答案

        Args:
            query: 查询字符串

        Returns:
            list: 答案列表
        """
        print(f"-> 搜索答案: {query}")

        try:
            from search import search_answers

            results = search_answers(query, top_k=10)

            print(f"  [OK] 找到 {len(results)} 个答案")

            return results

        except Exception as e:
            print(f"  [X] 搜索失败: {e}")
            import traceback
            traceback.print_exc()
            return []

    def process_question(self, region=(100, 200, 500, 600), show_image=False):
        """
        处理题目的完整流程

        Args:
            region: 题目区域坐标 (x1, y1, x2, y2)
            show_image: 是否显示截图（用于调试）

        Returns:
            dict: 包含答案和详细信息
        """
        result = {
            'success': False,
            'question_text': '',
            'answers': [],
            'best_answer': '',
            'error': ''
        }

        print("\n" + "="*60)
        print("开始答题流程")
        print("="*60)

        # 1. 截图
        print("\n[步骤1] 截取屏幕")
        screen_path = self.capture_screen()

        if not screen_path:
            result['error'] = '截图失败'
            return result

        if show_image:
            # 在Windows上用默认程序打开图片
            os.startfile(screen_path)

        # 2. 裁剪
        print("\n[步骤2] 裁剪题目区域")
        cropped_path = self.crop_region(screen_path, region)

        if not cropped_path:
            result['error'] = '裁剪失败'
            return result

        # 3. OCR识别
        print("\n[步骤3] OCR识别")
        question_text = self.ocr_recognize(cropped_path)

        if not question_text:
            result['error'] = 'OCR识别失败'
            return result

        result['question_text'] = question_text

        # 4. 搜索答案
        print("\n[步骤4] 搜索答案")
        answers = self.search_answer(question_text)

        if not answers:
            result['error'] = '未找到答案'
            return result

        # 5. 整理结果
        result['success'] = True
        result['answers'] = answers
        result['best_answer'] = answers[0]['answer']

        # 显示结果
        print("\n" + "="*60)
        print("识别结果")
        print("="*60)
        print(f"题目: {question_text}")
        print(f"\n最佳答案: {result['best_answer']}")

        print("\n候选答案:")
        for i, item in enumerate(answers, 1):
            print(f"  {i}. [{item['method']}] {item['score']:.2f} - {item['answer']}")

        print("="*60)

        return result
