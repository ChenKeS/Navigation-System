import matplotlib
matplotlib.use('TkAgg')  # 强制使用 TkAgg 后端

import matplotlib.pyplot as plt
from matplotlib.backend_bases import MouseButton
from matplotlib.widgets import Button, TextBox
from model.graph import Graph
from algorithm.dijkstra import Dijkstra
from algorithm.traffic import TrafficAwarePathFinder
import threading
import time

import os
import tkinter as tk

# 解决中文显示问题
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun']
plt.rcParams['axes.unicode_minus'] = False


class MapDrawer:
    """地图绘制器 - 支持交通模拟"""

    def __init__(self, graph: Graph):
        self.graph = graph

        # 创建窗口
        self.fig = plt.figure(figsize=(13, 9), facecolor='#2c2c2c')

        # 创建菜单栏
        self._create_menu()

        # 地图区域（左侧）
        self.map_ax = self.fig.add_axes([0.05, 0.08, 0.60, 0.88], facecolor='#1e1e1e')

        # 控制面板区域（右侧）
        self.panel_ax = self.fig.add_axes([0.68, 0.08, 0.28, 0.88], facecolor='#3c3c3c')
        self.panel_ax.axis('off')

        # 状态栏
        self.status_ax = self.fig.add_axes([0.05, 0.02, 0.60, 0.04])
        self.status_ax.axis('off')

        # 缩放相关
        self.zoom_level = 1.0
        self.center_x = 500
        self.center_y = 500

        # 选点相关
        self.selected_start = None
        self.selected_end = None
        self.highlighted_path = []

        # 交通模拟相关
        self.traffic_enabled = False
        self.traffic_thread = None
        self.running = False

        # 绑定事件
        self._bind_events()

        # 创建控制面板
        self._create_panel()

        # 绘制地图
        self.draw()
        self._update_status('系统就绪 | 左键选起点 右键选终点 滚轮缩放', '#888888')

    def _bind_events(self):
        self.fig.canvas.mpl_connect('scroll_event', self._on_scroll)
        self.fig.canvas.mpl_connect('button_press_event', self._on_click)

    def _create_panel(self):
        """创建控制面板"""
        y_pos = 0.94

        # 标题
        self.panel_ax.text(0.5, y_pos, '导航控制系统', transform=self.panel_ax.transAxes,
                           fontsize=14, fontweight='bold', ha='center', va='center', color='white')
        y_pos -= 0.05

        # 分隔线
        self.panel_ax.plot([0.1, 0.9], [y_pos, y_pos], color='gray', linewidth=0.8,
                           transform=self.panel_ax.transAxes)
        y_pos -= 0.05

        # 起点
        self.panel_ax.text(0.08, y_pos, '起点:', transform=self.panel_ax.transAxes,
                           fontsize=11, color='#4CAF50', fontweight='bold')
        start_ax = self.fig.add_axes([0.75, self._get_y(y_pos), 0.20, 0.045])  # x 从 0.35 改为 0.40
        self.start_textbox = TextBox(start_ax, '', initial='', color='#2c2c2c', hovercolor='#4c4c4c')
        self.start_textbox.on_submit(self._on_start_submit)
        y_pos -= 0.06

        # 终点
        self.panel_ax.text(0.08, y_pos, '终点:', transform=self.panel_ax.transAxes,
                           fontsize=11, color='#f44336', fontweight='bold')
        end_ax = self.fig.add_axes([0.75, self._get_y(y_pos), 0.20, 0.045])  # x 从 0.35 改为 0.40
        self.end_textbox = TextBox(end_ax, '', initial='', color='#2c2c2c', hovercolor='#4c4c4c')
        self.end_textbox.on_submit(self._on_end_submit)
        y_pos -= 0.07

        # 计算按钮
        calc_ax = self.fig.add_axes([0.70, self._get_y(y_pos), 0.25, 0.05])  # x 从 0.15 改为 0.20
        self.calc_button = Button(calc_ax, '计算最短路径', color='#2196F3', hovercolor='#1976D2')
        self.calc_button.on_clicked(self._on_calc_clicked)
        y_pos -= 0.065

        # 交通模拟开关
        traffic_ax = self.fig.add_axes([0.70, self._get_y(y_pos), 0.25, 0.05])  # x 从 0.15 改为 0.20
        self.traffic_button = Button(traffic_ax, '开启交通模拟', color='#FF9800', hovercolor='#F57C00')
        self.traffic_button.on_clicked(self._on_traffic_clicked)
        y_pos -= 0.065

        # 缩放控制标题
        self.panel_ax.text(0.08, y_pos, '缩放控制:', transform=self.panel_ax.transAxes,
                           fontsize=11, color='white', fontweight='bold')
        y_pos -= 0.06

        # 放大按钮
        zoom_in_ax = self.fig.add_axes([0.70, self._get_y(y_pos), 0.10, 0.045])  # x 从 0.15 改为 0.20
        self.zoom_in_button = Button(zoom_in_ax, '放大', color='#607D8B', hovercolor='#455A64')
        self.zoom_in_button.on_clicked(self._on_zoom_in)

        # 缩小按钮
        zoom_out_ax = self.fig.add_axes([0.85, self._get_y(y_pos), 0.10, 0.045])  # x 从 0.50 改为 0.55
        self.zoom_out_button = Button(zoom_out_ax, '缩小', color='#607D8B', hovercolor='#455A64')
        self.zoom_out_button.on_clicked(self._on_zoom_out)
        y_pos -= 0.055

        # 重置按钮
        reset_ax = self.fig.add_axes([0.70, self._get_y(y_pos), 0.25, 0.045])  # x 从 0.30 改为 0.35
        self.reset_button = Button(reset_ax, '重置视图', color='#9E9E9E', hovercolor='#757575')
        self.reset_button.on_clicked(self._on_reset)
        y_pos -= 0.07

        # 分隔线
        self.panel_ax.plot([0.1, 0.9], [y_pos, y_pos], color='gray', linewidth=0.8,
                           transform=self.panel_ax.transAxes)
        y_pos -= 0.05

        # 地图信息标题
        self.panel_ax.text(0.08, y_pos, '地图信息', transform=self.panel_ax.transAxes,
                           fontsize=11, fontweight='bold', color='#2196F3')
        y_pos -= 0.05

        # 地图信息
        self.panel_ax.text(0.08, y_pos, f'顶点数: {self.graph.get_vertex_count()}',
                           transform=self.panel_ax.transAxes, fontsize=10, color='#CCCCCC')
        y_pos -= 0.05
        self.panel_ax.text(0.08, y_pos, f'边数: {self.graph.get_edge_count()}',
                           transform=self.panel_ax.transAxes, fontsize=10, color='#CCCCCC')
        y_pos -= 0.05
        self.panel_ax.text(0.08, y_pos, f'缩放: {self.zoom_level:.1f}x',
                           transform=self.panel_ax.transAxes, fontsize=10, color='#CCCCCC')
        y_pos -= 0.08

        # 路径信息标题
        self.panel_ax.text(0.08, y_pos, '路径信息', transform=self.panel_ax.transAxes,
                           fontsize=11, fontweight='bold', color='#FF5722')
        y_pos -= 0.05

        # 路径信息
        self.path_text1 = self.panel_ax.text(0.08, y_pos, '路径: 未计算',
                                             transform=self.panel_ax.transAxes, fontsize=9, color='#888888')
        y_pos -= 0.05
        self.path_text2 = self.panel_ax.text(0.08, y_pos, '距离: --',
                                             transform=self.panel_ax.transAxes, fontsize=9, color='#888888')
        y_pos -= 0.05
        self.path_text3 = self.panel_ax.text(0.08, y_pos, '途经点: --',
                                             transform=self.panel_ax.transAxes, fontsize=9, color='#888888')
        y_pos -= 0.08

        # 交通状况标题
        self.panel_ax.text(0.08, y_pos, '交通状况', transform=self.panel_ax.transAxes,
                           fontsize=11, fontweight='bold', color='#FF9800')
        y_pos -= 0.05

        # 交通信息
        self.traffic_text1 = self.panel_ax.text(0.08, y_pos, '畅通: -- 条',
                                                transform=self.panel_ax.transAxes, fontsize=9, color='#00FF00')
        y_pos -= 0.05
        self.traffic_text2 = self.panel_ax.text(0.08, y_pos, '正常: -- 条',
                                                transform=self.panel_ax.transAxes, fontsize=9, color='#ADFF2F')
        y_pos -= 0.05
        self.traffic_text3 = self.panel_ax.text(0.08, y_pos, '拥挤: -- 条',
                                                transform=self.panel_ax.transAxes, fontsize=9, color='#FFA500')
        y_pos -= 0.05
        self.traffic_text4 = self.panel_ax.text(0.08, y_pos, '拥堵: -- 条',
                                                transform=self.panel_ax.transAxes, fontsize=9, color='#FF0000')

    def _get_y(self, y_pos):
        return 0.08 + 0.88 * y_pos

    def _update_traffic_display(self):
        """更新交通信息显示"""
        from algorithm.traffic import TrafficAwarePathFinder
        stats = TrafficAwarePathFinder.get_traffic_stats(self.graph)

        if stats and self.graph.get_edge_count() > 0:
            levels = stats['levels']
            self.traffic_text1.set_text(f'畅通: {levels[0]} 条')
            self.traffic_text2.set_text(f'正常: {levels[1]} 条')
            self.traffic_text3.set_text(f'拥挤: {levels[2]} 条')
            self.traffic_text4.set_text(f'拥堵: {levels[3]} 条')
        else:
            self.traffic_text1.set_text('畅通: 0 条')
            self.traffic_text2.set_text('正常: 0 条')
            self.traffic_text3.set_text('拥挤: 0 条')
            self.traffic_text4.set_text('拥堵: 0 条')

        try:
            self.fig.canvas.draw_idle()
        except:
            pass

    def _update_path_display(self, path, value, is_time_mode=False):
        """更新路径信息显示"""
        path_str = '->'.join(map(str, path[:6]))
        if len(path) > 6:
            path_str += '...'

        self.path_text1.set_text(f'路径: {path_str}')

        if is_time_mode:
            self.path_text2.set_text(f'时间: {value:.1f}')
        else:
            self.path_text2.set_text(f'距离: {value:.2f}')

        self.path_text3.set_text(f'途经点: {len(path)} 个')
        try:
            self.fig.canvas.draw_idle()
        except:
            pass

    def _clear_path_display(self):
        """清除路径信息显示"""
        self.path_text1.set_text('路径: 未计算')
        self.path_text2.set_text('距离: --')
        self.path_text3.set_text('途经点: --')
        try:
            self.fig.canvas.draw_idle()
        except:
            pass

    def _on_start_submit(self, text):
        try:
            vid = int(text)
            if 0 <= vid < self.graph.get_vertex_count():
                self.selected_start = vid
                self._update_status(f'已设置起点: {vid}', '#4CAF50')
                self.draw()
            else:
                self._update_status(f'顶点 {vid} 不存在', '#f44336')
        except ValueError:
            self._update_status('请输入数字', '#f44336')

    def _on_end_submit(self, text):
        try:
            vid = int(text)
            if 0 <= vid < self.graph.get_vertex_count():
                self.selected_end = vid
                self._update_status(f'已设置终点: {vid}', '#f44336')
                self.draw()
            else:
                self._update_status(f'顶点 {vid} 不存在', '#f44336')
        except ValueError:
            self._update_status('请输入数字', '#f44336')

    def _on_calc_clicked(self, event):
        if self.selected_start is None:
            self._update_status('请先设置起点', '#f44336')
            return
        if self.selected_end is None:
            self._update_status('请先设置终点', '#f44336')
            return

        self._update_status('正在计算路径...', '#FF9800')

        if self.traffic_enabled:
            path, time_cost = TrafficAwarePathFinder.shortest_time_path(
                self.graph, self.selected_start, self.selected_end
            )
            if path:
                self.set_highlight_path(path)
                self._update_status(f'路径计算完成 | 预计时间: {time_cost:.1f}', '#4CAF50')
                self._update_path_display(path, time_cost, is_time_mode=True)
            else:
                self._update_status('无法到达终点', '#f44336')
        else:
            path, distance = Dijkstra.shortest_path(self.graph, self.selected_start, self.selected_end)
            if path:
                self.set_highlight_path(path)
                self._update_status(f'路径计算完成 | 距离: {distance:.2f}', '#4CAF50')
                self._update_path_display(path, distance, is_time_mode=False)
            else:
                self._update_status('无法到达终点', '#f44336')

    def _traffic_simulation_loop(self):
        """交通模拟循环"""
        import random
        while self.running:
            time.sleep(1.0)
            if self.traffic_enabled:
                # 更新每条边的车辆数
                for edge in self.graph.edges:
                    change = random.uniform(-0.5, 0.5)
                    edge.update_traffic(change)
                # 刷新界面
                self._refresh_ui()

    def _refresh_ui(self):
        """刷新界面"""
        try:
            self.draw()
            self._update_traffic_display()

            if self.selected_start is not None and self.selected_end is not None:
                if self.traffic_enabled:
                    path, time_cost = TrafficAwarePathFinder.shortest_time_path(
                        self.graph, self.selected_start, self.selected_end
                    )
                    if path:
                        self.highlighted_path = path
                        self._update_path_display(path, time_cost, is_time_mode=True)
                else:
                    path, distance = Dijkstra.shortest_path(
                        self.graph, self.selected_start, self.selected_end
                    )
                    if path:
                        self.highlighted_path = path
                        self._update_path_display(path, distance, is_time_mode=False)
        except:
            pass

    def _on_traffic_clicked(self, event):
        self.traffic_enabled = not self.traffic_enabled

        if self.traffic_enabled:
            self.traffic_button.label.set_text('关闭交通模拟')
            self._update_status('交通模拟已开启 | 道路颜色代表拥堵程度', '#FF9800')

            # 开启时给一个随机车流，让颜色立即变化
            import random
            for edge in self.graph.edges:
                # 随机给 0 到 capacity*1.2 的车流
                edge.vehicle_count = random.uniform(0, edge.capacity * 1.2)

            # 启动模拟线程
            if self.traffic_thread is None or not self.traffic_thread.is_alive():
                self.running = True
                self.traffic_thread = threading.Thread(target=self._traffic_simulation_loop, daemon=True)
                self.traffic_thread.start()
        else:
            self.traffic_button.label.set_text('开启交通模拟')
            self.traffic_button.color = '#FF9800'
            self.running = False
            # 关闭时重置车流为0
            for edge in self.graph.edges:
                edge.vehicle_count = 0
            self._update_status('交通模拟已关闭', '#888888')

        if self.selected_start is not None and self.selected_end is not None:
            self._on_calc_clicked(None)

        self.draw()
        self._update_traffic_display()

    def _on_zoom_in(self, event):
        self.zoom_level *= 1.2
        self.zoom_level = min(5.0, self.zoom_level)
        self.draw()

    def _on_zoom_out(self, event):
        self.zoom_level /= 1.2
        self.zoom_level = max(0.5, self.zoom_level)
        self.draw()

    def _on_reset(self, event):
        self.zoom_level = 1.0
        self.center_x = 500
        self.center_y = 500
        self.draw()
        self._update_status('视图已重置', '#888888')

    def _update_status(self, message, color):
        self.status_ax.clear()
        self.status_ax.axis('off')
        self.status_ax.text(0, 0, message, fontsize=9, color=color)
        try:
            self.fig.canvas.draw_idle()
        except:
            pass

    def _on_scroll(self, event):
        scale_factor = 1.1
        if event.button == 'up':
            self.zoom_level *= scale_factor
        elif event.button == 'down':
            self.zoom_level /= scale_factor
        self.zoom_level = max(0.5, min(5.0, self.zoom_level))
        self.draw()

    def _on_click(self, event):
        if event.inaxes != self.map_ax:
            return

        min_dist = float('inf')
        closest = None

        for v in self.graph.vertices:
            x_data, y_data = self.map_ax.transData.inverted().transform((event.x, event.y))
            dist = ((v.x - x_data) ** 2 + (v.y - y_data) ** 2) ** 0.5
            if dist < min_dist and dist < 20:
                min_dist = dist
                closest = v

        if closest is not None:
            if event.button == MouseButton.LEFT:
                self.selected_start = closest.vid
                self._update_status(f'已选择起点: {closest.vid}', '#4CAF50')
                self.start_textbox.set_val(str(closest.vid))
            elif event.button == MouseButton.RIGHT:
                self.selected_end = closest.vid
                self._update_status(f'已选择终点: {closest.vid}', '#f44336')
                self.end_textbox.set_val(str(closest.vid))

            if self.selected_start is not None and self.selected_end is not None:
                self._on_calc_clicked(None)

            self.draw()

    def draw(self):
        self.map_ax.clear()
        self.map_ax.set_facecolor('#1e1e1e')

        range_x = 500 / self.zoom_level
        range_y = 400 / self.zoom_level
        x_min = self.center_x - range_x
        x_max = self.center_x + range_x
        y_min = self.center_y - range_y
        y_max = self.center_y + range_y

        # 画边
        for u in range(self.graph.get_vertex_count()):
            x1 = self.graph.vertices[u].x
            y1 = self.graph.vertices[u].y
            if x1 < x_min or x1 > x_max or y1 < y_min or y1 > y_max:
                continue

            for v, edge_id in self.graph.get_neighbors(u):
                if u < v:
                    x2 = self.graph.vertices[v].x
                    y2 = self.graph.vertices[v].y
                    if (x2 < x_min - 100 or x2 > x_max + 100 or
                            y2 < y_min - 100 or y2 > y_max + 100):
                        continue

                    edge = self.graph.get_edge_by_id(edge_id)
                    if edge:
                        if self._is_on_path(u, v):
                            self.map_ax.plot([x1, x2], [y1, y2], '#FF5722', linewidth=3.5, alpha=0.9, zorder=4)
                        else:
                            color = edge.get_color()
                            self.map_ax.plot([x1, x2], [y1, y2], color, linewidth=1.5, alpha=0.7, zorder=1)

        # 画点
        for v in self.graph.vertices:
            if x_min <= v.x <= x_max and y_min <= v.y <= y_max:
                if v.vid == self.selected_start:
                    self.map_ax.scatter(v.x, v.y, c='#4CAF50', s=120, zorder=5, marker='o', edgecolors='white',
                                        linewidth=2)
                elif v.vid == self.selected_end:
                    self.map_ax.scatter(v.x, v.y, c='#f44336', s=120, zorder=5, marker='o', edgecolors='white',
                                        linewidth=2)
                else:
                    self.map_ax.scatter(v.x, v.y, c='#2196F3', s=40, zorder=5, marker='o', alpha=0.8)

                text_color = 'white' if v.vid in [self.selected_start, self.selected_end] else '#CCCCCC'
                self.map_ax.annotate(str(v.vid), (v.x, v.y), fontsize=8, ha='center',
                                     va='center', color=text_color, fontweight='bold', zorder=6)

        self.map_ax.set_xlim(x_min, x_max)
        self.map_ax.set_ylim(y_min, y_max)
        self.map_ax.set_aspect('equal')
        self.map_ax.grid(True, alpha=0.2, color='white')
        self.map_ax.set_xlabel('')
        self.map_ax.set_ylabel('')
        self.map_ax.set_xticks([])
        self.map_ax.set_yticks([])

        title = f'导航地图 | 顶点: {self.graph.get_vertex_count()} | 边: {self.graph.get_edge_count()}'
        if self.traffic_enabled:
            title += ' | 交通模拟中 (绿=畅通 黄绿=正常 橙=拥挤 红=拥堵)'
        self.map_ax.set_title(title, color='white', fontsize=11, pad=8)

        try:
            self.fig.canvas.draw()
        except:
            pass

    def _is_on_path(self, u: int, v: int) -> bool:
        if not self.highlighted_path:
            return False
        for i in range(len(self.highlighted_path) - 1):
            if (u == self.highlighted_path[i] and v == self.highlighted_path[i + 1]) or \
                    (u == self.highlighted_path[i + 1] and v == self.highlighted_path[i]):
                return True
        return False

    def set_highlight_path(self, path: list):
        self.highlighted_path = path
        self.draw()

    def _create_menu(self):
        """创建菜单栏"""
        # 获取 matplotlib 的 figure 窗口
        manager = self.fig.canvas.manager
        if manager is None:
            return

        # 获取 tkinter 根窗口（因为用的是 TkAgg 后端）
        try:
            root = manager.window
            menubar = tk.Menu(root)
            root.config(menu=menubar)

            # 文件菜单
            file_menu = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="文件", menu=file_menu)
            file_menu.add_command(label="保存地图", command=self._on_save_map)
            file_menu.add_command(label="加载地图", command=self._on_load_map)
            file_menu.add_separator()
            file_menu.add_command(label="退出", command=self._on_exit)
        except:
            pass  # 如果获取不到窗口，跳过

    def _update_panel_info(self):
        """更新面板信息"""
        # 更新地图信息区域的文字
        # 找到地图信息的文本对象并更新
        for child in self.panel_ax.texts:
            text = child.get_text()
            if '顶点数:' in text:
                child.set_text(f'顶点数: {self.graph.get_vertex_count()}')
            elif '边数:' in text:
                child.set_text(f'边数: {self.graph.get_edge_count()}')
            elif '缩放:' in text:
                child.set_text(f'缩放: {self.zoom_level:.1f}x')
        try:
            self.fig.canvas.draw_idle()
        except:
            pass

    def _on_save_map(self, event = None):
        """保存地图"""
        from tkinter import filedialog
        import tkinter as tk
        import os

        # 先弹出对话框让用户选择保存位置
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="保存地图",
            initialdir=os.getcwd()  # 默认当前目录
        )

        if filepath:
            from file_io.file_manager import FileManager
            if FileManager.save_map(self.graph, filepath):
                self._update_status(f'地图已保存: {os.path.basename(filepath)}', '#4CAF50')
                # 打印完整路径，方便查找
                print(f"文件已保存到: {filepath}")
            else:
                self._update_status('保存失败', '#f44336')
        else:
            self._update_status('已取消保存', '#888888')

    def _on_load_map(self , event = None):
        """加载地图"""
        from tkinter import filedialog
        import tkinter as tk

        filepath = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="加载地图"
        )
        if filepath:
            from file_io.file_manager import FileManager
            new_graph = FileManager.load_map(filepath)
            if new_graph:
                self.graph = new_graph
                # 重置选点和路径
                self.selected_start = None
                self.selected_end = None
                self.highlighted_path = []
                self.draw()
                self._update_panel_info()
                self._update_traffic_display()
                self._clear_path_display()
                self._update_status(f'加载成功: {os.path.basename(filepath)}', '#4CAF50')
            else:
                self._update_status('加载失败', '#f44336')

    def _on_exit(self):
        """退出程序"""
        import sys
        sys.exit(0)

    def show(self):
        try:
            plt.show()
        except:
            pass