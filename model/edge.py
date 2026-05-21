class Edge:
    """边类 - 代表一条道路"""

    def __init__(self, u: int, v: int, length: float):
        """
        创建一条边
        :param u: 起点顶点ID
        :param v: 终点顶点ID
        :param length: 道路长度
        """
        self.u = u
        self.v = v
        self.length = length

        # 交通模拟属性
        self.capacity = 10.0  # 道路容量（最多同时容纳的车辆数）
        self.vehicle_count = 0.0  # 当前车辆数
        self.threshold = 0.8  # 拥堵阈值（n/v > 0.8 开始拥堵）

        # 常数系数
        self.c = 1.0  # 时间系数

        # 缓存当前通行时间
        self._current_time = length

    def get_congestion_ratio(self) -> float:
        """获取拥堵系数 n/v"""
        if self.capacity == 0:
            return 1.0
        return self.vehicle_count / self.capacity

    def get_congestion_level(self) -> int:
        """
        获取拥堵等级
        0: 畅通 (n/v <= 0.5)
        1: 正常 (0.5 < n/v <= 0.8)
        2: 拥挤 (0.8 < n/v <= 1.0)
        3: 拥堵 (n/v > 1.0)
        """
        ratio = self.get_congestion_ratio()
        if ratio <= 0.5:
            return 0  # 畅通
        elif ratio <= self.threshold:
            return 1  # 正常
        elif ratio <= 1.0:
            return 2  # 拥挤
        else:
            return 3  # 拥堵

    def get_color(self) -> str:
        """根据拥堵程度返回颜色"""
        level = self.get_congestion_level()
        colors = {
            0: '#00FF00',  # 绿色 - 畅通
            1: '#ADFF2F',  # 黄绿色 - 正常
            2: '#FFA500',  # 橙色 - 拥挤
            3: '#FF0000'  # 红色 - 拥堵
        }
        return colors.get(level, '#555555')

    def get_travel_time(self) -> float:
        """
        计算通行时间
        公式: t = c * L * f(n/v)
        f(x) = 1 (x <= threshold)
        f(x) = 1 + e^x (x > threshold)
        """
        import math
        ratio = self.get_congestion_ratio()

        if ratio <= self.threshold:
            f = 1.0
        else:
            # 拥堵时指数增长
            f = 1.0 + math.exp(ratio)
            # 限制最大倍数，避免过于夸张
            f = min(f, 10.0)

        return self.c * self.length * f

    def update_traffic(self, delta_vehicles: float):
        """
        更新车辆数
        :param delta_vehicles: 车辆数变化（正为增加，负为减少）
        """
        self.vehicle_count += delta_vehicles
        # 确保车辆数不为负
        if self.vehicle_count < 0:
            self.vehicle_count = 0

        # 更新通行时间
        self._current_time = self.get_travel_time()

    def get_current_time(self) -> float:
        """获取当前通行时间"""
        return self._current_time

    def to_dict(self) -> dict:
        """转换为字典，用于保存"""
        return {
            'u': self.u,
            'v': self.v,
            'length': self.length,
            'capacity': self.capacity,
            'vehicle_count': self.vehicle_count,
            'threshold': self.threshold,
            'c': self.c
        }

    @staticmethod
    def from_dict(data: dict) -> 'Edge':
        """从字典创建边"""
        edge = Edge(data['u'], data['v'], data['length'])
        edge.capacity = data.get('capacity', 10.0)
        edge.vehicle_count = data.get('vehicle_count', 0.0)
        edge.threshold = data.get('threshold', 0.8)
        edge.c = data.get('c', 1.0)
        return edge

    def __repr__(self):
        level_names = ['畅通', '正常', '拥挤', '拥堵']
        return f"Edge({self.u}->{self.v}, len={self.length:.1f}, {level_names[self.get_congestion_level()]}, vehicles={self.vehicle_count:.1f}/{self.capacity})"