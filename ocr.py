"""
OCR识别模块
输入：裁剪后的图片（文件路径或PIL Image对象）
输出：识别出的文字字符串
"""

import os
from typing import Union
from PIL import Image
import numpy as np


class OCRRecognizer:
    """OCR识别器"""

    def __init__(self, engine='easyocr'):
        """
        初始化OCR识别器

        Args:
            engine: OCR引擎类型 ('easyocr', 'paddleocr', 'tesseract')
        """
        self.engine = engine
        self._ocr = None
        self._init_engine()

    def _init_engine(self):
        """初始化OCR引擎"""
        if self.engine == 'easyocr':
            try:
                import easyocr
                self._ocr = easyocr.Reader(['ch_sim', 'en'], gpu=False)
                print(f"[OCR] EasyOCR引擎初始化成功")
            except ImportError:
                raise ImportError("EasyOCR未安装，请运行: pip install easyocr")

        elif self.engine == 'paddleocr':
            try:
                from paddleocr import PaddleOCR
                self._ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
                print(f"[OCR] PaddleOCR引擎初始化成功")
            except ImportError:
                raise ImportError("PaddleOCR未安装，请运行: pip install paddleocr")

        else:
            raise ValueError(f"不支持的OCR引擎: {self.engine}")

    def recognize(self, image_input: Union[str, Image.Image, np.ndarray]) -> str:
        """
        识别图片中的文字

        Args:
            image_input: 输入图片，可以是：
                - 文件路径 (str)
                - PIL Image对象
                - numpy数组

        Returns:
            识别出的文字字符串
        """
        # 处理不同类型的输入
        img = self._load_image(image_input)

        # 根据引擎类型进行识别
        if self.engine == 'easyocr':
            return self._recognize_with_easyocr(img)
        elif self.engine == 'paddleocr':
            return self._recognize_with_paddleocr(img)

    def _load_image(self, image_input: Union[str, Image.Image, np.ndarray]) -> np.ndarray:
        """加载图片为numpy数组"""
        if isinstance(image_input, str):
            # 文件路径
            if not os.path.exists(image_input):
                raise FileNotFoundError(f"图片文件不存在: {image_input}")
            img = Image.open(image_input)
            return np.array(img)

        elif isinstance(image_input, Image.Image):
            # PIL Image
            return np.array(image_input)

        elif isinstance(image_input, np.ndarray):
            # numpy数组
            return image_input

        else:
            raise TypeError(f"不支持的输入类型: {type(image_input)}")

    def _recognize_with_easyocr(self, img: np.ndarray) -> str:
        """使用EasyOCR识别"""
        results = self._ocr.readtext(img)

        # 提取所有文字，按位置排序
        if results:
            # 按y坐标排序（从上到下）
            sorted_results = sorted(results, key=lambda x: x[0][0][1])
            texts = [result[1] for result in sorted_results]
            return ''.join(texts)

        return ""

    def _recognize_with_paddleocr(self, img: np.ndarray) -> str:
        """使用PaddleOCR识别"""
        result = self._ocr.ocr(img, cls=True)

        if result and result[0]:
            # 按y坐标排序
            sorted_results = sorted(result[0], key=lambda x: x[0][0][1])
            texts = [line[1][0] for line in sorted_results]
            return ''.join(texts)

        return ""


# ===================== API =====================

# 全局OCR实例
_ocr_instance = None


def init_ocr(engine='easyocr'):
    """
    初始化OCR引擎（全局单例）

    Args:
        engine: OCR引擎类型 ('easyocr', 'paddleocr')
    """
    global _ocr_instance
    _ocr_instance = OCRRecognizer(engine)
    return _ocr_instance


def recognize_text(image_input, engine='easyocr') -> str:
    """
    识别图片中的文字（API）

    Args:
        image_input: 输入图片，支持：
            - 文件路径 (str): 'path/to/image.png'
            - PIL Image对象
            - numpy数组
        engine: OCR引擎类型 ('easyocr', 'paddleocr')

    Returns:
        识别出的文字字符串

    Examples:
        >>> # 使用文件路径
        >>> text = recognize_text('question.png')
        >>> print(text)

        >>> >>> # 使用PIL Image
        >>> from PIL import Image
        >>> img = Image.open('question.png')
        >>> text = recognize_text(img)
        >>> print(text)

        >>> >>> # 使用numpy数组
        >>> import numpy as np
        >>> img_array = np.array(Image.open('question.png'))
        >>> text = recognize_text(img_array)
        >>> print(text)
    """
    global _ocr_instance

    # 如果没有初始化，自动初始化
    if _ocr_instance is None or _ocr_instance.engine != engine:
        _ocr_instance = OCRRecognizer(engine)

    return _ocr_instance.recognize(image_input)


if __name__ == "__main__":
    # 测试代码
    import sys

    if len(sys.argv) < 2:
        print("用法: python ocr.py <图片路径>")
        print("示例: python ocr.py question.png")
        sys.exit(1)

    image_path = sys.argv[1]

    try:
        # 识别图片
        text = recognize_text(image_path)
        print(f"识别结果: {text}")

    except Exception as e:
        print(f"识别失败: {e}")
        sys.exit(1)
