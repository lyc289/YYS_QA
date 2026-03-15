"""
自动答题循环 - 持续监控并答题
"""

import os
import sys
import time

project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from simple_answer_helper import EnhancedAnswerHelper


def auto_answer_loop():
    """
    自动答题循环
    """

    print("""
╔════════════════════════════════════════════════════════════╗
║          自动答题循环模式                                    ║
║          连接真实设备                                         ║
║          按Ctrl+C停止                                        ║
╚════════════════════════════════════════════════════════════╝
    """)

    try:
        helper = EnhancedAnswerHelper()
    except SystemExit:
        print("\n设备连接失败，程序退出")
        return

    # 题目区域（从配置读取）
    region_config = helper.config.get('question_region', {})
    question_region = (
        region_config.get('x1', 100),
        region_config.get('y1', 200),
        region_config.get('x2', 500),
        region_config.get('y2', 600)
    )

    print(f"题目区域: {question_region} (从config.json读取)")
    print("循环间隔: 3秒")
    print("-"*60)

    count = 0

    try:
        while True:  # 无限循环，直到用户按Ctrl+C
            count += 1
            print(f"\n[第{count}次] {time.strftime('%H:%M:%S')}")
            print("-"*60)

            # 处理题目
            result = helper.process_question(question_region)

            if result['success']:
                print(f"\n[OK] 识别成功！")
                print(f"题目: {result['question_text']}")
                print(f"\n前2个最高分答案:")

                # 显示前2个最高分的结果
                for i, item in enumerate(result['answers'][:2], 1):
                    print(f"\n{i}. 答案: {item['answer']}")
                    print(f"   分数: {item['score']:.2f}")
                    print(f"   匹配方式: {item['method']}")
                    print(f"   原问题: {item['question']}")

            else:
                print(f"\n[X] {result['error']}")

            # 等待用户按回车继续
            try:
                input("\n按回车键继续识别下一题...")
            except EOFError:
                # 非交互模式，自动继续
                print("\n(非交互模式，3秒后自动继续)")
                time.sleep(3)

    except KeyboardInterrupt:
        print(f"\n\n用户中断，共处理{count}次")

    print(f"\n程序结束，共处理{count}次")


if __name__ == "__main__":
    auto_answer_loop()
