"""
测试裁剪区域 - 手动调试坐标参数
输入格式: x1,y1,x2,y2 (例如: 100,200,500,600)
"""

import os
import sys

# 添加项目路径
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from PIL import Image

# 创建img文件夹
img_dir = os.path.join(project_dir, "img")
os.makedirs(img_dir, exist_ok=True)


def test_crop_region(image_path, region):
    """
    测试裁剪区域

    Args:
        image_path: 原截图路径
        region: (x1, y1, x2, y2) 裁剪区域

    Returns:
        裁剪后的图片路径
    """
    output_path = os.path.join(img_dir, "crop_test_result.png")

    print(f"\n-> 裁剪区域: {region}")
    print(f"   原图: {image_path}")

    try:
        # 打开图片
        img = Image.open(image_path)
        print(f"   原图尺寸: {img.size}")

        # 调整坐标（防止超出范围）
        x1, y1, x2, y2 = region
        width, height = img.size

        x1 = max(0, min(x1, width))
        y1 = max(0, min(y1, height))
        x2 = max(0, min(x2, width))
        y2 = max(0, min(y2, height))

        if x1 >= x2 or y1 >= y2:
            print(f"   [X] 坐标无效: ({x1},{y1}) -> ({x2},{y2})")
            return None

        # 裁剪
        cropped = img.crop((x1, y1, x2, y2))
        print(f"   裁剪尺寸: {cropped.size}")

        # 保存
        cropped.save(output_path)
        print(f"   [OK] 保存到: {output_path}")

        # 自动打开图片
        os.startfile(output_path)

        return output_path

    except Exception as e:
        print(f"   [X] 裁剪失败: {e}")
        return None


def main():
    print("="*60)
    print("裁剪区域测试工具")
    print("="*60)

    # 加载配置文件获取默认区域
    import json
    config_path = os.path.join(project_dir, "config.json")
    default_region = (100, 200, 500, 600)  # 默认值

    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        region_config = config.get('question_region', {})
        default_region = (
            region_config.get('x1', 100),
            region_config.get('y1', 200),
            region_config.get('x2', 500),
            region_config.get('y2', 600)
        )
        print(f"从config.json读取默认区域: {default_region}")
    else:
        print(f"未找到config.json，使用默认区域: {default_region}")

    # 查找最新的截图文件
    import glob
    png_files = glob.glob(os.path.join(img_dir, "temp_screen_*.png"))
    if not png_files:
        print(f"\n[X] 未找到截图文件")
        print(f"请先运行 auto_answer_loop.py 截取屏幕")
        print(f"或手动将截图放入 img/ 文件夹")
        return

    # 使用最新的截图
    image_path = max(png_files, key=os.path.getmtime)
    print(f"使用截图: {os.path.basename(image_path)}")


    # 显示原图信息
    img = Image.open(image_path)
    print(f"图片尺寸: {img.size[0]} x {img.size[1]}")

    print(f"\n当前默认区域: {default_region}")
    print(f"格式: x1,y1,x2,y2 (左上角x, 左上角y, 右下角x, 右下角y)")
    print(f"说明: (0,0) 是左上角")

    while True:
        print("\n" + "-"*60)
        user_input = input(f"输入区域 (回车使用默认 {default_region}, q退出): ").strip()

        if user_input.lower() == 'q':
            print("退出")
            break

        if not user_input:
            region = default_region
        else:
            try:
                parts = [int(x.strip()) for x in user_input.split(',')]
                if len(parts) != 4:
                    raise ValueError("需要4个数值")
                region = tuple(parts)
            except ValueError as e:
                print(f"[X] 输入格式错误: {e}")
                print("    正确格式: 100,200,500,600")
                continue

        result = test_crop_region(image_path, region)

        if result:
            # 更新默认为最后一次成功的值
            default_region = region


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except EOFError:
        print("\n\n非交互模式退出")
