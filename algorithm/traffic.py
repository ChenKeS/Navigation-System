import heapq
import math


class TrafficAwarePathFinder:
    """考虑交通状况的路径查找器（F5）"""

    @staticmethod
    def shortest_time_path(graph, start: int, end: int):
        """
        基于通行时间的最短路径（考虑交通拥堵）
        返回: (path_list, total_time)
        """
        n = graph.get_vertex_count()
        dist = [float('inf')] * n
        prev = [-1] * n
        dist[start] = 0

        pq = [(0, start)]

        while pq:
            d, u = heapq.heappop(pq)

            if d > dist[u]:
                continue

            if u == end:
                break

            for v, edge_id in graph.get_neighbors(u):
                edge = graph.get_edge_by_id(edge_id)
                # 使用通行时间作为权重（不是距离）
                travel_time = edge.get_current_time()
                new_dist = dist[u] + travel_time

                if new_dist < dist[v]:
                    dist[v] = new_dist
                    prev[v] = u
                    heapq.heappush(pq, (new_dist, v))

        if dist[end] == float('inf'):
            return [], float('inf')

        # 重建路径
        path = []
        curr = end
        while curr != -1:
            path.append(curr)
            curr = prev[curr]
        path.reverse()

        return path, dist[end]

    @staticmethod
    def simulate_traffic_flow(graph, steps: int = 10):
        """模拟交通流随时间变化"""
        import random
        for step in range(steps):
            for edge in graph.edges:
                # 随机增加或减少车辆数
                change = random.uniform(-0.8, 0.8)
                new_count = edge.vehicle_count + change
                # 确保车辆数在 0 到 capacity*1.5 之间
                edge.vehicle_count = max(0, min(edge.capacity * 1.5, new_count))

            if steps <= 20:
                congested = sum(1 for e in graph.edges if e.get_congestion_level() >= 2)
                print(f"Step {step + 1}: {congested}/{graph.get_edge_count()} 条道路拥堵")

    @staticmethod
    def get_traffic_stats(graph):
        """获取交通统计信息"""
        if graph.get_edge_count() == 0:
            return {}

        levels = [0, 0, 0, 0]  # 畅通、正常、拥挤、拥堵
        total_time = 0
        total_length = 0

        for edge in graph.edges:
            level = edge.get_congestion_level()
            levels[level] += 1
            total_time += edge.get_current_time()
            total_length += edge.length

        return {
            'levels': levels,
            'avg_time_ratio': total_time / total_length if total_length > 0 else 1.0,
            'congested_ratio': (levels[2] + levels[3]) / graph.get_edge_count()
        }