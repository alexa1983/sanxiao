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
                                button_width, button_height, font=self.font),
            'ready': Button("准备", start_x + button_width + button_spacing, first_row_y, 
                           button_width, button_height, active=False, font=self.font),
            'start': Button("开始游戏", start_x, right_panel_bottom, 
                           button_width, button_height, active=False, font=self.font),
            'leave': Button("离开房间", start_x + button_width + button_spacing, right_panel_bottom, 
                           button_width, button_height, active=False, font=self.font)
        }
        
        # 缓存常用文本
        self.cached_texts = {
            'left_title': self.font.render("在线玩家", True, (255, 255, 255)),
            'right_title': self.font.render("房间信息", True, (255, 255, 255)),
            'no_room': self.small_font.render("请创建或加入房间", True, (200, 200, 200))
        }
        
        # 开始搜索局域网玩家
        self.start_discovery()
        
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
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 处理玩家列表点击
            if self.left_panel.collidepoint(event.pos):
                list_y = event.pos[1] - self.left_panel.top + self.scroll_offset
                index = int(list_y // 45)
                if 0 <= index < len(self.online_players):
                    self.selected_player = list(self.online_players.values())[index]
            
            # 处理按钮点击
            for name, button in self.buttons.items():
                if button.clicked(event.pos):
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
        for player in self.online_players.values():
            if y + 40 >= 0 and y <= 500:
                if player == self.selected_player:
                    pygame.draw.rect(self.left_surface, (60, 60, 80),
                                   (5, y, 370, 35))
                
                name = self.small_font.render(player.name, True, (255, 255, 255))
                status = self.small_font.render(player.status, True,
                                              (100, 255, 100) if player.status == "在线"
                                              else (255, 100, 100))
                
                self.left_surface.blit(name, (15, y + 8))
                self.left_surface.blit(status, (200, y + 8))
            y += 45
        
        # 绘制房间信息到右面板
        self.right_surface.fill((40, 40, 60))
        if self.current_room:
            room_info = [
                f"房间号: {self.current_room.room_id}",
                f"房主: {self.current_room.host.name}",
                f"玩家2: {self.current_room.guest.name if self.current_room.guest else '等待加入'}",
                f"状态: {self.current_room.status}"
            ]
            
            y = 60
            for info in room_info:
                text = self.small_font.render(info, True, (200, 200, 200))
                self.right_surface.blit(text, (10, y))
                y += 30
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
        
        # 使用双缓冲更新显示
        pygame.display.flip() 
    
    def handle_button_click(self, button_name):
        """处理按钮点击事件"""
        try:
            if button_name == 'refresh':
                self.refresh_player_list()
            elif button_name == 'create_room':
                self.create_room()
            elif button_name == 'ready':
                self.toggle_ready()
            elif button_name == 'start':
                self.start_game()
            elif button_name == 'leave':
                self.leave_room()
            
        except Exception as e:
            print(f"按钮点击处理错误: {e}")
            import traceback
            traceback.print_exc()