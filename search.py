"""
问答检索模块
输入：查询字符串
输出：答案列表（按相关性排序，优先保证召回率）
"""

import json
import re
from difflib import SequenceMatcher
from typing import List, Dict


class QASearcher:
    """问答检索器"""

    def __init__(self, qa_json_path: str = 'qa_bank.json'):
        """
        初始化检索器

        Args:
            qa_json_path: 问答数据JSON文件路径
        """
        self.qa_json_path = qa_json_path
        self.qa_list = []
        self._load_data()
        self._build_indexes()

    def _load_data(self):
        """加载问答数据"""
        with open(self.qa_json_path, 'r', encoding='utf-8') as f:
            qa_dict = json.load(f)

        self.qa_list = [{"question": q, "answer": a} for q, a in qa_dict.items()]
        print(f"[Search] 加载了 {len(self.qa_list)} 条问答数据")

    def _build_indexes(self):
        """构建检索索引"""
        # 标准化问题列表
        self.normalized_questions = [
            self._normalize_text(item["question"])
            for item in self.qa_list
        ]

        # 标准化答案列表
        self.normalized_answers = [
            self._normalize_text(item["answer"])
            for item in self.qa_list
        ]

        # 提取关键词
        self.question_keywords = [
            set(self._extract_keywords(item["question"]))
            for item in self.qa_list
        ]

        self.answer_keywords = [
            set(self._extract_keywords(item["answer"]))
            for item in self.qa_list
        ]

    def _normalize_text(self, text: str) -> str:
        """标准化文本：去除标点"""
        text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', text)
        return text

    def _extract_keywords(self, text: str) -> list:
        """提取关键词（2-4字词语）"""
        norm_text = self._normalize_text(text)
        words = []
        for i in range(len(norm_text)):
            for j in range(i+2, min(i+5, len(norm_text)+1)):
                word = norm_text[i:j]
                if len(word) >= 2:
                    words.append(word)
        return words

    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        搜索答案（多级检索，保证召回率）

        Args:
            query: 查询字符串
            top_k: 返回的最大结果数

        Returns:
            答案列表，每个元素包含：
            {
                'question': str,      # 匹配的问题
                'answer': str,        # 答案
                'score': float,       # 匹配分数 (0-1)
                'method': str         # 匹配方法
            }
        """
        if not query or not query.strip():
            return []

        results = []

        # Level 1: 完全匹配（权重最高）
        exact_results = self._exact_match_search(query)
        for result in exact_results:
            results.append({
                'question': result['question'],
                'answer': result['answer'],
                'score': 1.0,
                'method': 'exact'
            })

        # Level 2: 关键词匹配
        keyword_results = self._keyword_match_search(query)
        for result in keyword_results:
            # 避免重复
            if not any(r['question'] == result['question'] for r in results):
                results.append({
                    'question': result['question'],
                    'answer': result['answer'],
                    'score': result['score'],
                    'method': 'keyword'
                })

        # Level 3: 模糊匹配（如果前面结果不够）
        if len(results) < top_k:
            fuzzy_results = self._fuzzy_match_search(query)
            for result in fuzzy_results:
                # 避免重复
                if not any(r['question'] == result['question'] for r in results):
                    results.append({
                        'question': result['question'],
                        'answer': result['answer'],
                        'score': result['score'],
                        'method': 'fuzzy'
                    })

        # 按分数排序并返回top_k
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]

    def _exact_match_search(self, query: str) -> List[Dict]:
        """完全匹配检索"""
        norm_query = self._normalize_text(query)
        results = []

        for i, norm_q in enumerate(self.normalized_questions):
            # 完全相等
            if norm_query == norm_q:
                results.append(self.qa_list[i])
                continue

            # 包含匹配
            if len(norm_query) >= 4:
                if norm_query in norm_q:
                    results.append(self.qa_list[i])
                elif norm_q in norm_query:
                    results.append(self.qa_list[i])

        return results

    def _keyword_match_search(self, query: str) -> List[Dict]:
        """关键词匹配检索"""
        keywords = set(self._extract_keywords(query))
        keywords = {k for k in keywords if len(k) >= 2}

        if not keywords:
            return []

        scores = []

        # 在问题中匹配
        for i, q_keywords in enumerate(self.question_keywords):
            intersection = keywords & q_keywords
            if intersection:
                score = len(intersection) / len(keywords)
                if score >= 0.3:  # 降低阈值提高召回率
                    scores.append((score, i, self.qa_list[i]))

        # 在答案中匹配
        for i, a_keywords in enumerate(self.answer_keywords):
            intersection = keywords & a_keywords
            if intersection:
                score = len(intersection) / len(keywords) * 0.9  # 答案匹配权重稍低
                if score >= 0.3:
                    scores.append((score, i, self.qa_list[i]))

        # 去重并排序
        seen = set()
        unique_scores = []
        for score, i, item in scores:
            if item['question'] not in seen:
                seen.add(item['question'])
                unique_scores.append((score, i, item))

        unique_scores.sort(key=lambda x: x[0], reverse=True)

        return [{'question': item['question'], 'answer': item['answer'], 'score': score}
                for score, i, item in unique_scores]

    def _fuzzy_match_search(self, query: str) -> List[Dict]:
        """模糊匹配检索"""
        norm_query = self._normalize_text(query)

        if len(norm_query) < 2:
            return []

        scores = []

        for i, norm_q in enumerate(self.normalized_questions):
            ratio = SequenceMatcher(None, norm_query, norm_q).ratio()

            # 长度惩罚
            len_diff = abs(len(norm_query) - len(norm_q))
            if len(norm_query) > 0:
                length_penalty = len_diff / max(len(norm_query), len(norm_q))
                adjusted_ratio = ratio * (1 - length_penalty * 0.3)
            else:
                adjusted_ratio = ratio

            if adjusted_ratio >= 0.4:  # 降低阈值提高召回率
                scores.append((adjusted_ratio, i, self.qa_list[i]))

        scores.sort(key=lambda x: x[0], reverse=True)

        return [{'question': item['question'], 'answer': item['answer'], 'score': score}
                for score, i, item in scores]


# ===================== API =====================

# 全局检索实例
_searcher_instance = None


def init_search(qa_json_path='qa_bank.json'):
    """
    初始化检索器（全局单例）

    Args:
        qa_json_path: 问答数据JSON文件路径
    """
    global _searcher_instance
    _searcher_instance = QASearcher(qa_json_path)
    return _searcher_instance


def search_answers(query: str, top_k: int = 10, qa_json_path='qa_bank.json') -> List[Dict]:
    """
    搜索答案（API）

    Args:
        query: 查询字符串
        top_k: 返回的最大结果数（默认10，保证召回率）
        qa_json_path: 问答数据JSON文件路径

    Returns:
        答案列表，按相关性排序，每个元素包含：
        {
            'question': str,      # 匹配的问题
            'answer': str,        # 答案
            'score': float,       # 匹配分数 (0-1)
            'method': str         # 匹配方法 ('exact', 'keyword', 'fuzzy')
        }

    Examples:
        >>> # 搜索答案
        >>> results = search_answers('弱冠是指多少岁')
        >>> for r in results:
        ...     print(f"{r['answer']} (分数: {r['score']:.2f})")

        >>> >>> # 获取最佳答案
        >>> best_answer = search_answers('弱冠是指多少岁', top_k=1)[0]['answer']
        >>> print(best_answer)  # 输出: 20岁

        >>> >>> # 获取所有候选答案
        >>> results = search_answers('茨木呱 气球')
        >>> answers = [r['answer'] for r in results]
        >>> print(answers)
    """
    global _searcher_instance

    # 如果没有初始化，自动初始化
    if _searcher_instance is None:
        _searcher_instance = QASearcher(qa_json_path)

    return _searcher_instance.search(query, top_k)


def get_best_answer(query: str, qa_json_path='qa_bank.json') -> str:
    """
    获取最佳答案（API）

    Args:
        query: 查询字符串
        qa_json_path: 问答数据JSON文件路径

    Returns:
        最佳答案字符串，如果未找到返回空字符串

    Examples:
        >>> answer = get_best_answer('弱冠是指多少岁')
        >>> print(answer)  # 输出: 20岁
    """
    results = search_answers(query, top_k=1, qa_json_path=qa_json_path)
    return results[0]['answer'] if results else ""


if __name__ == "__main__":
    # 测试代码
    import sys

    if len(sys.argv) < 2:
        print("用法: python search.py <查询字符串>")
        print("示例: python search.py '弱冠是指多少岁'")
        sys.exit(1)

    query = sys.argv[1]

    try:
        # 搜索答案
        results = search_answers(query)

        print(f"查询: {query}")
        print(f"找到 {len(results)} 个结果:\n")

        for i, result in enumerate(results, 1):
            print(f"{i}. [{result['method']}] 分数: {result['score']:.2f}")
            print(f"   问题: {result['question']}")
            print(f"   答案: {result['answer']}")
            print()

    except Exception as e:
        print(f"搜索失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
