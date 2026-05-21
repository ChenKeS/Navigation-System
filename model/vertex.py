class Vertex:
    def __init__(self , vid : int , x : float , y : float):
        """
                创建一个顶点
                :param vid: 顶点编号 (0, 1, 2, ...)
                :param x: X坐标
                :param y: Y坐标
                """
        self.vid = vid
        self.x = x
        self.y = y

    def calculate_dist(self , other : "Vertex") -> float:
        """计算到另一个顶点的欧氏距离"""
        dx = self.x - other.x
        dy = self.y - other.y
        return (dx * dx + dy * dy) ** 0.5

    def to_dict(self) -> dict:
        """转换为字典，用于保存"""
        return {
            'vid': self.vid,
            'x': self.x,
            'y': self.y
        }

    @staticmethod
    def from_dict(data: dict) -> 'Vertex':
        """从字典创建顶点"""
        return Vertex(data['vid'], data['x'], data['y'])

    def __repr__(self):
        return f"Vertex({self.vid} , {self.x:.2f} , {self.y:.2f})"