import random
import math
from model.vertex import Vertex
from model.edge import Edge


class Graph:
    """图类 - 存储整个地图，支持交通模拟"""

    def __init__(self):
        self.vertices = []  # 顶点列表
        self.adjacency = []  # 邻接表: adjacency[u] = [(v, edge_id), ...]
        self.edges = []  # 边列表: edges[edge_id] = Edge对象
        self.edge_index = {}  # 边索引: (u, v) -> edge_id

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

        # 2. 初始化
        self.adjacency = [[] for _ in range(n)]
        self.edges = []
        self.edge_index = {}

        # 3. 每个点连接到最近的k个点
        for i in range(n):
            distances = []
            for j in range(n):
                if j != i:
                    dist = self.vertices[i].calculate_dist(self.vertices[j])
                    distances.append((dist, j))

            distances.sort()
            for dist, j in distances[:k]:
                if not self._has_edge(i, j):
                    self._add_edge(i, j, dist)

        # 4. 确保连通
        self._ensure_connectivity()

        # 5. 添加随机车流（让交通模拟有颜色变化）


    def _add_edge(self, u: int, v: int, length: float):
        """添加双向边"""
        edge_id = len(self.edges)
        edge = Edge(u, v, length)

        self.edges.append(edge)
        self.edge_index[(u, v)] = edge_id
        self.edge_index[(v, u)] = edge_id

        self.adjacency[u].append((v, edge_id))
        self.adjacency[v].append((u, edge_id))

    def _has_edge(self, u: int, v: int) -> bool:
        """检查边是否存在"""
        return (u, v) in self.edge_index

    def get_edge(self, u: int, v: int) -> Edge:
        """获取两个顶点之间的边"""
        edge_id = self.edge_index.get((u, v))
        if edge_id is not None:
            return self.edges[edge_id]
        return None

    def get_edge_by_id(self, edge_id: int) -> Edge:
        """根据ID获取边"""
        return self.edges[edge_id]

    def get_edge_color(self, u: int, v: int) -> str:
        """获取边的颜色（用于绘制）"""
        edge = self.get_edge(u, v)
        if edge:
            return edge.get_color()
        return '#555555'

    def _ensure_connectivity(self):
        """确保图连通"""
        visited = [False] * len(self.vertices)
        components = []

        for i in range(len(self.vertices)):
            if not visited[i]:
                comp = self._bfs(i, visited)
                components.append(comp)

        for i in range(len(components) - 1):
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
        """BFS遍历"""
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
        return len(self.vertices)

    def get_edge_count(self) -> int:
        return len(self.edges)

    def get_vertex(self, vid: int) -> Vertex:
        return self.vertices[vid]

    def get_neighbors(self, vid: int) -> list:
        """返回 (邻居ID, 边ID) 列表"""
        return self.adjacency[vid]

    def update_traffic(self, delta_time: float = 1.0):
        """
        更新交通模拟
        每帧调用，模拟车辆动态变化
        """
        import random
        for edge in self.edges:
            # 让车辆数在 0 到 capacity*1.5 之间波动
            # 这样颜色会有明显变化
            change = random.uniform(-1.5, 1.5) * delta_time
            new_count = edge.vehicle_count + change
            # 限制范围
            edge.vehicle_count = max(0, min(edge.capacity * 1.5, new_count))

    def get_path_edges(self, path: list) -> list:
        """根据顶点路径，返回经过的边列表"""
        edges = []
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edge = self.get_edge(u, v)
            if edge:
                edges.append(edge)
        return edges

    def to_dict(self) -> dict:
        """将整个图转换为字典"""
        return {
            'vertices': [v.to_dict() for v in self.vertices],
            'edges': [e.to_dict() for e in self.edges],
            'adjacency': self.adjacency
        }

    def from_dict(self, data: dict):
        """从字典恢复图"""
        # 恢复顶点
        self.vertices = [Vertex.from_dict(v_data) for v_data in data['vertices']]

        # 恢复边
        self.edges = [Edge.from_dict(e_data) for e_data in data['edges']]

        # 重建边索引
        self.edge_index = {}
        for i, edge in enumerate(self.edges):
            self.edge_index[(edge.u, edge.v)] = i
            self.edge_index[(edge.v, edge.u)] = i

        # 恢复邻接表
        self.adjacency = data['adjacency']
        if not self.adjacency:
            # 如果保存的数据没有 adjacency，重新构建
            self.adjacency = [[] for _ in range(len(self.vertices))]
            for edge in self.edges:
                edge_id = self.edge_index[(edge.u, edge.v)]
                self.adjacency[edge.u].append((edge.v, edge_id))
                self.adjacency[edge.v].append((edge.u, edge_id))

        # 更新边的通行时间缓存
        for edge in self.edges:
            edge._current_time = edge.get_travel_time()

    def __repr__(self):
        return f"Graph(vertices={self.get_vertex_count()}, edges={self.get_edge_count()})"