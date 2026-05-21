import json
import os


class FileManager:
    """文件管理器 - 负责保存和加载地图"""

    @staticmethod
    def save_map(graph, filepath: str) -> bool:
        """
        保存地图到文件
        :param graph: Graph对象
        :param filepath: 保存路径
        :return: 是否成功
        """
        try:
            data = graph.to_dict()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"地图已保存到: {filepath}")
            return True
        except Exception as e:
            print(f"保存失败: {e}")
            return False

    @staticmethod
    def load_map(filepath: str):
        """
        从文件加载地图
        :param filepath: 文件路径
        :return: Graph对象，失败返回None
        """
        try:
            if not os.path.exists(filepath):
                print(f"文件不存在: {filepath}")
                return None

            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            from model.graph import Graph
            graph = Graph()
            graph.from_dict(data)
            print(f"地图加载成功: {graph}")
            return graph
        except Exception as e:
            print(f"加载失败: {e}")
            return None