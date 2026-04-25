from model.graph import Graph
from ui.map_drawer import MapDrawer


def main():
    print("=" * 50)
    print("      数据结构课程设计 - 导航系统")
    print("=" * 50)

    print("\n正在生成地图...")
    graph = Graph()
    graph.generate_random(n=150, k=4)  # 150个点效果更好
    print(f"✓ 生成完成: {graph}")

    print("\n启动图形界面...")
    print("提示:")
    print("  - 左键点击地图: 选择起点")
    print("  - 右键点击地图: 选择终点")
    print("  - 鼠标滚轮: 缩放地图")
    print("  - 右侧面板: 输入顶点编号或使用按钮")

    drawer = MapDrawer(graph)
    drawer.show()


if __name__ == "__main__":
    main()