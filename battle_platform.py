import pygame
import socket
import threading
import time
import os
from constants import GameState

class Button:
    def __init__(self, text, x, y, width=200, height=50, active=True, font=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.active = active
        self.font = font or pygame.font.Font(None, 36)  # 使用传入的字体或默认字体
        self.color = (100, 100, 100)
        self.hover_color = (120, 120, 120)
        self.inactive_color = (50, 50, 50)
        self.is_hovered = False
        
    def draw(self, screen):
        # 确定按钮颜色
        if not self.active:
            color = self.inactive_color
        elif self.is_hovered:
            color = self.hover_color
        else:
            color = self.color
            
        # 绘制按钮背景
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2)  # 边框
        
        # 使用设定的字体绘制文本
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def update(self, mouse_pos):
        # 更新悬停状态
        self.is_hovered = self.rect.collidepoint(mouse_pos) and self.active
        
    def clicked(self, pos):
        return self.active and self.rect.collidepoint(pos)

class Player:
    def __init__(self, name, ip):
        self.name = name
        self.ip = ip
        self.status = "在线"  # 在线、游戏中、离线
        self.last_seen = time.time()

class Room:
    def __init__(self, host_player):
        self.host = host_player
        self.guest = None
        self.status = "等待中"  # 等待中、准备中、游戏中
        self.room_id = str(int(time.time()))

class BattlePlatform:
    def __init__(self, screen, network_manager):
        self.screen = screen
        self.network = network_manager
        
        # 初始化字体
        try:
            font_path = os.path.join('assets', 'simhei.ttf')
            if os.path.exists(font_path):
                self.font = pygame.font.Font(font_path, 24)        # 从36调整到24
                self.small_font = pygame.font.Font(font_path, 20)  # 从24调整到20
            else:
                font_names = ['SimHei', 'Microsoft YaHei', 'PingFang SC']
                font_loaded = False
                for font_name in font_names:
                    try:
                        self.font = pygame.font.SysFont(font_name, 24)        # 从36调整到24
                        self.small_font = pygame.font.SysFont(font_name, 20)  # 从24调整到20
                        font_loaded = True
                        break
                    except:
                        continue
                
                if not font_loaded:
                    self.font = pygame.font.Font(None, 24)        # 从36调整到24
                    self.small_font = pygame.font.Font(None, 20)  # 从24调整到20
        except Exception as e:
            print(f"字体加载错误: {e}")
            self.font = pygame.font.Font(None, 24)        # 从36调整到24
            self.small_font = pygame.font.Font(None, 20)  # 从24调整到20
        
        # 定义左右两栏的区域（使用固定尺寸）
        self.left_panel = pygame.Rect(20, 50, 380, 500)
        self.right_panel = pygame.Rect(420, 50, 360, 500)
        
        # 创建背景surface
        self.background = pygame.Surface(self.screen.get_size())
        self.background = self.background.convert()
        self.background.fill((30, 30, 50))
        
        # 创建面板surface
        self.left_surface = pygame.Surface((380, 500))
        self.right_surface = pygame.Surface((360, 500))
        
        # 玩家列表
        self.online_players = {}
        self.current_room = None
        self.scroll_offset = 0
        self.selected_player = None
        
        # 调整按钮位置和尺寸
        button_width = 100    # 按钮宽度
        button_height = 32    # 按钮高度
        button_spacing = 10   # 按钮之间的水平间距
        
        # 计算右侧面板底部的按钮位置
        right_panel_bottom = self.right_panel.bottom - button_height - 10  # 距离底部10像素
        first_row_y = right_panel_bottom - button_height - 10  # 第一行按钮的y坐标
        
        # 计算按钮的x坐标（两个按钮一行，居中对齐）
        total_width = button_width * 2 + button_spacing  # 每行两个按钮的总宽度
        start_x = self.right_panel.x + (self.right_panel.width - total_width) // 2
        
        # 重新定义按钮位置（两行按钮，每行两个）
        self.buttons = {
            'refresh': Button("刷新列表", 30, 520, button_width, button_height, font=self.font),
            'create_room': Button("创建房间", start_x, first_row_y, 
                                button_width, button_height, font=self.font)
        }
        
        # 缓存常用文本
        self.cached_texts = {
            'left_title': self.font.render("在线玩家", True, (255, 255, 255)),
            'right_title': self.font.render("房间信息", True, (255, 255, 255)),
            'no_room': self.small_font.render("请创建或加入房间", True, (200, 200, 200))
        }
        
        # 开始搜索局域网玩家
        self.start_discovery()
        
        # 添加更新计时器
        self.last_update = 0
        self.update_interval = 1.0  # 每秒更新一次
        
        self.rooms = {}  # 存储可见的房间
        
        # 创建房间浮窗
        self.room_overlay = RoomOverlay(screen, network_manager, self.font)
        
    def start_discovery(self):
        """开始搜索局域网玩家"""
        threading.Thread(target=self.discover_players, daemon=True).start()
        
    def discover_players(self):
        """搜索局域网玩家"""
        while True:
            try:
                # 广播自己的存在
                self.network.broadcast_presence()
                
                # 更新在线玩家状态
                current_time = time.time()
                for ip, player in list(self.online_players.items()):
                    if current_time - player.last_seen > 5:  # 5秒未响应视为离线
                        del self.online_players[ip]
                
                time.sleep(2)  # 每2秒更新一次
            except Exception as e:
                print(f"发现玩家出错: {e}")
                
    def handle_event(self, event):
        # 如果在房间中，优先处理房间事件
        if self.network.current_room:
            if self.room_overlay.handle_event(event):
                if self.network.current_room.status == "游戏中":
                    # 切换到游戏状态
                    return "START_GAME"
                # 如果返回True但不是开始游戏，表示离开房间
                self.network.current_room = None
            return
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 处理玩家列表点击
            if self.left_panel.collidepoint(event.pos):
                list_y = event.pos[1] - self.left_panel.top + self.scroll_offset
                index = int(list_y // 45)
                if 0 <= index < len(self.online_players):
                    self.selected_player = list(self.online_players.values())[index]
                    print(f"选中玩家: {self.selected_player}")
            
            # 处理房间加入点击
            elif self.right_panel.collidepoint(event.pos):
                mouse_pos = event.pos
                relative_y = mouse_pos[1] - self.right_panel.y
                
                # 遍历房间列表检查点击
                y = 60
                for room_id, room in self.rooms.items():
                    if room.status == "等待中":  # 只处理等待中的房间
                        join_button_rect = pygame.Rect(
                            self.right_panel.x + 300,  # 加入按钮的x位置
                            self.right_panel.y + y,    # 房间项的y位置
                            50,                        # 按钮宽度
                            25                         # 按钮高度
                        )
                        
                        if join_button_rect.collidepoint(mouse_pos):
                            print(f"尝试加入房间: {room_id}")
                            if self.network.join_room(room_id, room.host.ip):
                                self.current_room = room
                                print(f"成功加入房间: {room_id}")
                            break
                    y += 60
            
            # 处理其他按钮点击
            for name, button in self.buttons.items():
                if button.clicked(event.pos):
                    if name == 'refresh':
                        self.network.broadcast_presence()
                        self.update()
                    else:
                        self.handle_button_click(name)
                    
        elif event.type == pygame.MOUSEWHEEL:
            # 只在鼠标在玩家列表区域时处理滚动
            if self.left_panel.collidepoint(pygame.mouse.get_pos()):
                self.scroll_offset = max(0, min(
                    self.scroll_offset - event.y * 20,
                    max(0, len(self.online_players) * 45 - self.left_panel.height)
                ))
        
    def refresh_player_list(self):
        """刷新玩家列表"""
        self.network.request_player_list()
        
    def create_room(self):
        """创建游戏房间"""
        local_player = Player("本地玩家", self.network.get_local_ip())
        self.current_room = Room(local_player)
        self.buttons['ready'].active = True
        self.buttons['leave'].active = True
        
    def toggle_ready(self):
        """切换准备状态"""
        if self.current_room:
            self.network.send_ready_state(not self.network.is_ready)
            
    def can_start_game(self):
        """检查是否可以开始游戏"""
        return (self.current_room and 
                self.current_room.guest and 
                self.network.is_ready and 
                self.network.opponent_ready)
                
    def start_game(self):
        """开始游戏"""
        if self.can_start_game():
            self.network.send_data({'type': 'start_game'})
            
    def leave_room(self):
        """离开房间"""
        if self.current_room:
            self.network.send_data({'type': 'leave_room'})
            self.current_room = None
            self.buttons['ready'].active = False
            self.buttons['start'].active = False
            self.buttons['leave'].active = False
            
    def handle_player_selection(self, mouse_pos):
        """处理玩家选择"""
        y = mouse_pos[1] - self.player_list_rect.top + self.scroll_offset
        index = int(y // 40)
        if 0 <= index < len(self.online_players):
            self.selected_player = list(self.online_players.values())[index]
            
    def invite_player(self, player):
        """邀请玩家"""
        if self.current_room and not self.current_room.guest:
            self.network.send_invite(player.ip)
            
    def update(self):
        """更新游戏状态"""
        current_time = time.time()
        if current_time - self.last_update >= self.update_interval:
            self.last_update = current_time
            
            # 更新玩家列表和房间列表
            if self.network:
                self.online_players = {p.ip: p for p in self.network.players}
                self.rooms = self.network.rooms
                
                # 更新房间浮窗
                if self.network.current_room:
                    self.room_overlay.update()
    
    def draw(self):
        # 绘制基础背景
        self.screen.blit(self.background, (0, 0))
        
        # 绘制左右面板背景
        pygame.draw.rect(self.screen, (40, 40, 60), self.left_panel)
        pygame.draw.rect(self.screen, (40, 40, 60), self.right_panel)
        
        # 绘制标题
        self.screen.blit(self.cached_texts['left_title'], (30, 20))
        self.screen.blit(self.cached_texts['right_title'], (430, 20))
        
        # 绘制玩家列表到左面板
        self.left_surface.fill((40, 40, 60))
        y = 10 - self.scroll_offset
        
        # 使用online_players字典而不是network.players
        for player in self.online_players.values():
            if y + 40 >= 0 and y <= 500:
                if player == self.selected_player:
                    pygame.draw.rect(self.left_surface, (60, 60, 80),
                                   (5, y, 370, 35))
                
                # 绘制玩家信息
                name_text = self.small_font.render(f"{player.name}", True, (255, 255, 255))
                ip_text = self.small_font.render(f"{player.ip}", True, (200, 200, 200))
                status_text = self.small_font.render(player.status, True,
                                                   (100, 255, 100) if player.status == "在线"
                                                   else (255, 100, 100))
                
                self.left_surface.blit(name_text, (15, y + 8))
                self.left_surface.blit(ip_text, (150, y + 8))
                self.left_surface.blit(status_text, (280, y + 8))
            y += 45
        
        # 绘制房间列表到右面板
        self.right_surface.fill((40, 40, 60))
        if self.rooms:
            y = 60
            for room_id, room in self.rooms.items():
                # 跳过自己创建的房间
                if self.current_room and room_id == self.current_room.room_id:
                    continue
                    
                # 绘制房间基本信息
                room_text = self.small_font.render(
                    f"房间: {room_id[:8]}...",
                    True, (200, 200, 200)
                )
                host_text = self.small_font.render(
                    f"主机: {room.host.name}",
                    True, (200, 200, 200)
                )
                
                # 显示房间状态
                status_text = ""
                if room.status == "等待中":
                    status_text = "等待加入"
                elif room.status == "准备中":
                    if room.host_ready and room.guest_ready:
                        status_text = "全部准备"
                    else:
                        ready_count = sum([room.host_ready, room.guest_ready])
                        status_text = f"准备中({ready_count}/2)"
                else:
                    status_text = room.status
                
                status_render = self.small_font.render(
                    status_text,
                    True,
                    (100, 255, 100) if room.status == "等待中" else 
                    (255, 200, 100) if room.status == "准备中" else
                    (255, 100, 100)
                )
                
                self.right_surface.blit(room_text, (10, y))
                self.right_surface.blit(host_text, (10, y + 20))
                self.right_surface.blit(status_render, (10, y + 40))
                
                # 显示加入按钮（只对等待中的房间显示）
                if (room.status == "等待中" and 
                    not self.current_room and 
                    room.host.ip != self.network.get_local_ip()):
                    join_button = pygame.Rect(300, y, 50, 25)
                    mouse_pos = pygame.mouse.get_pos()
                    adjusted_pos = (
                        mouse_pos[0] - self.right_panel.x,
                        mouse_pos[1] - self.right_panel.y
                    )
                    
                    if join_button.collidepoint(adjusted_pos):
                        pygame.draw.rect(self.right_surface, (80, 80, 100), join_button)
                    else:
                        pygame.draw.rect(self.right_surface, (60, 60, 80), join_button)
                    
                    join_text = self.small_font.render("加入", True, (255, 255, 255))
                    text_rect = join_text.get_rect(center=join_button.center)
                    self.right_surface.blit(join_text, text_rect)
                
                y += 60
        else:
            self.right_surface.blit(self.cached_texts['no_room'], (10, 60))
        
        # 将面板surface绘制到屏幕
        self.screen.blit(self.left_surface, self.left_panel)
        self.screen.blit(self.right_surface, self.right_panel)
        
        # 绘制分隔线
        pygame.draw.line(self.screen, (60, 60, 80), 
                        (410, 10), (410, 580), 2)
        
        # 绘制按钮
        for button in self.buttons.values():
            button.draw(self.screen)
        
        # 绘制滚动条
        if len(self.online_players) * 45 > self.left_panel.height:
            scroll_height = self.left_panel.height
            scroll_pos = (self.scroll_offset / 
                         (len(self.online_players) * 45 - self.left_panel.height) * 
                         (scroll_height - 40))
            pygame.draw.rect(self.screen, (60, 60, 80),
                           (self.left_panel.right - 15, 
                            self.left_panel.top + scroll_pos, 10, 40))
        
        # 在最后绘制房间浮窗
        if self.network.current_room:
            self.room_overlay.draw()
        
        # 使用双缓冲更新显示
        pygame.display.flip() 
    
    def handle_button_click(self, button_name):
        """处理按钮点击事件"""
        try:
            if button_name == 'create_room':
                room = self.network.create_room()
                if room:
                    self.current_room = room
                    self.buttons['ready'].active = True
                    self.buttons['leave'].active = True
                    print("创建房间成功")
            
            elif button_name == 'ready':
                if self.current_room:
                    self.network.send_ready_state(not self.network.is_ready)
                    print(f"切换准备状态: {'已准备' if self.network.is_ready else '未准备'}")
            
            elif button_name == 'start':
                if self.can_start_game():
                    self.network.send_data({
                        'type': 'start_game',
                        'room_id': self.current_room.room_id
                    })
                    print("发送开始游戏请求")
            
            elif button_name == 'leave':
                if self.current_room:
                    self.network.send_data({
                        'type': 'leave_room',
                        'room_id': self.current_room.room_id,
                        'player_ip': self.network.get_local_ip()
                    })
                    self.current_room = None
                    self.buttons['ready'].active = False
                    self.buttons['start'].active = False
                    self.buttons['leave'].active = False
                    print("离开房间")
                    
        except Exception as e:
            print(f"按钮点击处理错误: {e}")
            import traceback
            traceback.print_exc()

class RoomView:
    def __init__(self, screen, room, network, font):
        self.screen = screen
        self.room = room
        self.network = network
        self.font = font
        self.player_states = {}  # 存储玩家状态
        self.opponent_score = 0
        self.opponent_moves = 0
        
    def update(self, game_state=None):
        """更新房间状态"""
        if game_state:
            if game_state['player_ip'] != self.network.get_local_ip():
                self.opponent_score = game_state['score']
                self.opponent_moves = game_state['moves_left']
    
    def draw(self):
        """绘制房间界面"""
        # 绘制房间信息面板
        panel = pygame.Surface((300, 200))
        panel.fill((40, 40, 60))
        
        # 绘制玩家信息
        y = 20
        # 房主信息
        host_text = self.font.render(f"房主: {self.room.host.name}", True, (255, 255, 255))
        host_status = self.font.render(
            "已准备" if self.network.is_ready else "未准备", 
            True, (100, 255, 100) if self.network.is_ready else (255, 100, 100)
        )
        panel.blit(host_text, (10, y))
        panel.blit(host_status, (200, y))
        
        # 客人信息
        if self.room.guest:
            y += 40
            guest_text = self.font.render(f"玩家: {self.room.guest.name}", True, (255, 255, 255))
            guest_status = self.font.render(
                "已准备" if self.network.opponent_ready else "未准备",
                True, (100, 255, 100) if self.network.opponent_ready else (255, 100, 100)
            )
            panel.blit(guest_text, (10, y))
            panel.blit(guest_status, (200, y))
        
        # 在游戏中显示对手信息
        if self.room.status == "游戏中":
            y += 40
            score_text = self.font.render(f"对手分数: {self.opponent_score}", True, (255, 255, 255))
            moves_text = self.font.render(f"对手步数: {self.opponent_moves}", True, (255, 255, 255))
            panel.blit(score_text, (10, y))
            panel.blit(moves_text, (200, y))
        
        # 绘制到屏幕
        self.screen.blit(panel, (250, 200))

class RoomOverlay:
    def __init__(self, screen, network, font):
        self.screen = screen
        self.network = network
        self.font = font
        
        # 浮窗位置和大小
        window_width, window_height = screen.get_size()
        self.width = 400
        self.height = 300
        self.x = (window_width - self.width) // 2
        self.y = (window_height - self.height) // 2
        
        # 创建浮窗surface
        self.surface = pygame.Surface((self.width, self.height))
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        # 创建房间内的按钮
        button_width = 120
        button_height = 40
        button_y = self.height - button_height - 20
        
        self.buttons = {
            'ready': Button("准备", self.x + 20, self.y + button_y, 
                          button_width, button_height, font=font),
            'start': Button("开始游戏", self.x + 150, self.y + button_y, 
                          button_width, button_height, active=False, font=font),
            'leave': Button("离开房间", self.x + 280, self.y + button_y, 
                          button_width, button_height, font=font)
        }
    
    def update(self):
        """更新房间状态和按钮"""
        if self.network.current_room:
            room = self.network.current_room
            # 更新准备按钮状态和文本
            is_ready = self.network.is_ready
            self.buttons['ready'].text = "取消准备" if is_ready else "准备"
            
            # 更新开始按钮状态
            is_host = room.host.ip == self.network.get_local_ip()
            can_start = (
                room.guest and                # 有客人加入
                room.host_ready and           # 房主已准备
                room.guest_ready and          # 客人已准备
                is_host                       # 是房主
            )
            self.buttons['start'].active = can_start
            
            # 更新房间状态显示
            if room.guest:
                if is_host:
                    room.host_ready = is_ready
                else:
                    room.guest_ready = is_ready
    
    def draw(self):
        """绘制房间浮窗"""
        if not self.network.current_room:
            return
            
        # 绘制半透明背景
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(128)
        self.screen.blit(overlay, (0, 0))
        
        # 绘制房间窗口
        self.surface.fill((40, 40, 60))
        pygame.draw.rect(self.surface, (60, 60, 80), (0, 0, self.width, self.height), 2)
        
        # 绘制房间信息
        room = self.network.current_room
        is_host = room.host.ip == self.network.get_local_ip()
        
        # 房间标题
        title = self.font.render(f"房间号: {room.room_id[:8]}...", True, (255, 255, 255))
        self.surface.blit(title, (20, 20))
        
        # 房间状态
        status_text = "等待玩家加入" if not room.guest else (
            "全部准备完成" if room.host_ready and room.guest_ready else "等待准备"
        )
        status = self.font.render(status_text, True, (200, 200, 200))
        self.surface.blit(status, (20, 140))
        
        # 房主信息
        host_text = self.font.render(f"房主: {room.host.name}", True, (255, 255, 255))
        host_ready = self.font.render(
            "√ 已准备" if room.host_ready else "× 未准备",
            True, (100, 255, 100) if room.host_ready else (255, 100, 100)
        )
        self.surface.blit(host_text, (20, 60))
        self.surface.blit(host_ready, (200, 60))
        
        # 客人信息
        if room.guest:
            guest_text = self.font.render(f"玩家: {room.guest.name}", True, (255, 255, 255))
            guest_ready = self.font.render(
                "√ 已准备" if room.guest_ready else "× 未准备",
                True, (100, 255, 100) if room.guest_ready else (255, 100, 100)
            )
            self.surface.blit(guest_text, (20, 100))
            self.surface.blit(guest_ready, (200, 100))
        else:
            waiting_text = self.font.render("等待玩家加入...", True, (200, 200, 200))
            self.surface.blit(waiting_text, (20, 100))
        
        # 绘制到屏幕
        self.screen.blit(self.surface, (self.x, self.y))
        
        # 绘制按钮
        for button in self.buttons.values():
            button.draw(self.screen)
    
    def handle_event(self, event):
        """处理房间内的事件"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            for name, button in self.buttons.items():
                if button.clicked(event.pos):
                    if name == 'ready':
                        # 切换准备状态
                        new_state = not self.network.is_ready
                        self.network.send_ready_state(new_state)
                        self.buttons['ready'].text = "取消准备" if new_state else "准备"
                    elif name == 'start' and button.active:
                        # 发送开始游戏消息
                        try:
                            self.network.send_data({
                                'type': 'start_game',
                                'room_id': self.network.current_room.room_id,
                                'host_ip': self.network.current_room.host.ip
                            })
                            self.network.current_room.status = "游戏中"
                            print("已发送开始游戏消息")
                            return True  # 返回True触发游戏开始
                        except Exception as e:
                            print(f"发送开始游戏消息失败: {e}")
                    elif name == 'leave':
                        self.network.send_data({
                            'type': 'leave_room',
                            'room_id': self.network.current_room.room_id,
                            'player_ip': self.network.get_local_ip()
                        })
                        return True  # 返回True表示离开房间
        return False