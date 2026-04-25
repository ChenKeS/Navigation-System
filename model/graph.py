import random
from model.vertex import Vertex


class Graph:
    """图类 - 存储整个地图"""

    def __init__(self):
        self.vertices = []  # 顶点列表
        self.adjacency = []  # 邻接表: adjacency[u] = [(v, weight), ...]

    def generate_random(self, n: int, k: int = 4):
        """
        随机生成一个连通图
        :param n: 顶点数量
        :param k: 每个顶点连接附近k个点的基数
        """
        # 1. 随机生成n个点 (坐标范围 0-1000)
        self.vertices = []
        for i in range(n):
            x = random.uniform(0, 1000)
            y = random.uniform(0, 1000)
            self.vertices.append(Vertex(i, x, y))

        # 2. 初始化邻接表
        self.adjacency = [[] for _ in range(n)]

        # 3. 每个点连接到最近的k个点（保证连通性）
        for i in range(n):
            # 计算所有其他点到i的距离
            distances = []
            for j in range(n):
                if j != i:
                    dist = self.vertices[i].calculate_dist(self.vertices[j])
                    distances.append((dist, j))

            # 按距离排序，取最近的k个
            distances.sort()
            for dist, j in distances[:k]:
                # 避免重复添加
                if not self._has_edge(i, j):
                    self._add_edge(i, j, dist)

        # 4. 检查连通性，如果不连通则补充边
        self._ensure_connectivity()

    def _add_edge(self, u: int, v: int, weight: float):
        """添加双向边"""
        self.adjacency[u].append((v, weight))
        self.adjacency[v].append((u, weight))

    def _has_edge(self, u: int, v: int) -> bool:
        """检查边是否存在"""
        for neighbor, _ in self.adjacency[u]:
            if neighbor == v:
                return True
        return False

    def _ensure_connectivity(self):
        """确保图连通（用BFS检查，不连通的地方加桥接边）"""
        # 找连通分量
        visited = [False] * len(self.vertices)
        components = []

        for i in range(len(self.vertices)):
            if not visited[i]:
                comp = self._bfs(i, visited)
                components.append(comp)

        # 如果有多个连通分量，连接它们
        for i in range(len(components) - 1):
            # 找两个分量中最近的两个点，连起来
            min_dist = float('inf')
            best_u, best_v = -1, -1

            for u in components[i]:
                for v in components[i + 1]:
                    dist = self.vertices[u].calculate_dist(self.vertices[v])
                    if dist < min_dist:
                        min_dist = dist
                        best_u, best_v = u, v

            self._add_edge(best_u, best_v, min_dist)

    def _bfs(self, start: int, visited: list) -> list:
        """BFS遍历，返回连通分量中的所有顶点"""
        queue = [start]
        visited[start] = True
        component = []

        while queue:
            u = queue.pop(0)
            component.append(u)
            for v, _ in self.adjacency[u]:
                if not visited[v]:
                    visited[v] = True
                    queue.append(v)

        return component

    def get_vertex_count(self) -> int:
        """获取顶点数量"""
        return len(self.vertices)

    def get_edge_count(self) -> int:
        """获取边的数量"""
        count = 0
        for neighbors in self.adjacency:
            count += len(neighbors)
        return count // 2  # 因为每条边被数了两次

    def get_vertex(self, vid: int) -> Vertex:
        """根据ID获取顶点"""
        return self.vertices[vid]

    def get_neighbors(self, vid: int) -> list:
        """获取某个顶点的所有邻居"""
        return self.adjacency[vid]

    def __repr__(self):
        return f"Graph(vertices={self.get_vertex_count()}, edges={self.get_edge_count()})"