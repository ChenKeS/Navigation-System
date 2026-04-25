import heapq


class Dijkstra:
    """Dijkstra 最短路径算法"""

    @staticmethod
    def shortest_path(graph, start: int, end: int):
        """
        计算从 start 到 end 的最短路径
        返回: (path_list, distance)
        """
        n = graph.get_vertex_count()
        dist = [float('inf')] * n
        prev = [-1] * n
        dist[start] = 0

        # 优先队列: (距离, 顶点)
        pq = [(0, start)]

        while pq:
            d, u = heapq.heappop(pq)

            if d > dist[u]:
                continue

            if u == end:
                break

            for v, weight in graph.get_neighbors(u):
                new_dist = dist[u] + weight
                if new_dist < dist[v]:
                    dist[v] = new_dist
                    prev[v] = u
                    heapq.heappush(pq, (new_dist, v))

        # 重建路径
        if dist[end] == float('inf'):
            return [], float('inf')

        path = []
        curr = end
        while curr != -1:
            path.append(curr)
            curr = prev[curr]
        path.reverse()

        return path, dist[end]