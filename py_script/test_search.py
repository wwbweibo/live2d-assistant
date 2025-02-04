import unittest
from unittest.mock import Mock, patch
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from py_script.search import DuckDuckGoSearchEngine
from py_script.llm import OllamaClient

class TestDuckDuckGoSearchEngine(unittest.TestCase):
    def setUp(self):
        """
        在每个测试用例执行前运行，初始化搜索引擎
        """
        # 创建一个模拟的 OllamaClient
        self.mock_ollama = OllamaClient('http://localhost:11434')
        self.search_engine = DuckDuckGoSearchEngine(self.mock_ollama)

    def test_init(self):
        """
        测试搜索引擎初始化
        """
        self.assertEqual(self.search_engine.engine_name, 'DuckDuckGO')
        self.assertIsNotNone(self.search_engine.ollama_client)

    # def test_search(self):
    #     """
    #     测试搜索功能
    #     """
    #     query = "测试查询"
    #     expected_result = "DuckDuckGo search result for 测试查询"
        
    #     result = self.search_engine.search(query)
        
    #     self.assertEqual(result, expected_result)

    def test_before_search(self):
        """
        测试搜索前的查询语句生成
        """
        test_text = "我想学习Python的单元测试"
        result = self.search_engine.before_search(test_text)
        print(result)
        result = self.search_engine.search(result)
        print(result)
        result = self.search_engine.find_top_bese_match_article(test_text, result)
        print(result)
        

    # def test_before_search_with_empty_text(self):
    #     """
    #     测试空文本的情况
    #     """
    #     self.mock_ollama.generate.return_value = ""
        
    #     result = self.search_engine.before_search("")
        
    #     self.assertEqual(result, "")

    # def test_before_search_with_special_characters(self):
    #     """
    #     测试包含特殊字符的情况
    #     """
    #     test_text = "Python!@#$%^&*()"
    #     self.mock_ollama.generate.return_value = "搜索：Python"
        
    #     result = self.search_engine.before_search(test_text)
        
    #     self.assertEqual(result, "搜索：Python")

if __name__ == '__main__':
    unittest.main() 
