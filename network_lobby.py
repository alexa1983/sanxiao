import pygame
import os
from constants import GameState

class InputBox:
    def __init__(self, x, y, width, height, placeholder="", font=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.color_inactive = pygame.Color('lightskyblue3')
        self.color_active = pygame.Color('dodgerblue2')
        self.color = self.color_inactive
        self.text = ""
        self.placeholder = placeholder
        self.font = font or pygame.font.Font(None, 32)
        self.active = False
        self.rendered_text = None
        self.cursor_visible = True
        self.cursor_timer = 0
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 如果用户点击了输入框内部
            if self.rect.collidepoint(event.pos):
                self.active = True
                self.color = self.color_active
            else:
                self.active = False
                self.color = self.color_inactive
                
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    self.active = False
                    self.color = self.color_inactive
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    # 限制文本长度，防止超出输入框
                    if len(self.text) < 20:  # 可以调整最大长度
                        self.text += event.unicode
                self.rendered_text = None  # 重新渲染文本
                
    def update(self):
        # 更新光标闪烁
        if pygame.time.get_ticks() - self.cursor_timer > 500:  # 每500ms闪烁一次
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = pygame.time.get_ticks()
            
    def draw(self, screen):
        # 绘制输入框
        pygame.draw.rect(screen, self.color, self.rect, 2)
        
        # 如果没有预渲染的文本，重新渲染
        if self.rendered_text is None:
            if self.text:
                self.rendered_text = self.font.render(self.text, True, (255, 255, 255))
            else:
                # 如果没有文本，显示占位符
                self.rendered_text = self.font.render(self.placeholder, True, (128, 128, 128))
        
        # 绘制文本
        text_rect = self.rendered_text.get_rect()
        text_rect.x = self.rect.x + 5
        text_rect.centery = self.rect.centery
        screen.blit(self.rendered_text, text_rect)
        
        # 如果输入框处于活动状态且光标可见，绘制光标
        if self.active and self.cursor_visible:
            cursor_pos = text_rect.right + 2
            if self.text:  # 只有在有文本时才显示光标
                pygame.draw.line(screen, self.color,
                               (cursor_pos, self.rect.y + 5),
                               (cursor_pos, self.rect.bottom - 5), 2)

class Button:
    def __init__(self, text, x, y, width=200, height=50, active=True, font=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.active = active
        self.font = font or pygame.font.Font(None, 36)
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
        
        # 绘制文本
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
        
    def update(self, mouse_pos):
        # 更新悬停状态
        self.is_hovered = self.rect.collidepoint(mouse_pos) and self.active
        
    def clicked(self, pos):
        return self.active and self.rect.collidepoint(pos)

class NetworkLobby:
    def __init__(self, screen, network_manager):
        self.screen = screen
        self.network = network_manager
        
        # 初始化字体
        try:
            # 尝试从assets目录加载自定义字体
            font_path = os.path.join('assets', 'simhei.ttf')  # 确保此文件存在
            if os.path.exists(font_path):
                self.font = pygame.font.Font(font_path, 36)
                self.small_font = pygame.font.Font(font_path, 24)
                print("NetworkLobby: 使用自定义字体文件")
            else:
                # 尝试系统中文字体
                font_names = [
                    'SimHei',           # Windows 黑体
                    'Microsoft YaHei',   # Windows 微软雅黑
                    'PingFang SC',      # macOS 苹方
                    'Noto Sans CJK SC', # Linux 思源黑体
                    'WenQuanYi Micro Hei', # Linux 文泉驿微米黑
                    'Heiti TC',         # macOS 黑体-繁
                    'Arial Unicode MS'  # 通用 Unicode 字体
                ]
                
                font_loaded = False
                for font_name in font_names:
                    try:
                        self.font = pygame.font.SysFont(font_name, 36)
                        self.small_font = pygame.font.SysFont(font_name, 24)
                        print(f"NetworkLobby: 使用系统字体: {font_name}")
                        font_loaded = True
                        break
                    except:
                        continue
                
                if not font_loaded:
                    print("NetworkLobby: 无法加载中文字体，使用默认字体")
                    self.font = pygame.font.Font(None, 36)
                    self.small_font = pygame.font.Font(None, 24)
        
        except Exception as e:
            print(f"NetworkLobby: 字体加载错误: {e}")
            self.font = pygame.font.Font(None, 36)
            self.small_font = pygame.font.Font(None, 24)
        
        # 测试字体渲染
        try:
            test_text = "测试文字"
            test_surface = self.font.render(test_text, True, (255, 255, 255))
            print("NetworkLobby: 字体渲染测试成功")
        except Exception as e:
            print(f"NetworkLobby: 字体渲染测试失败: {e}")
        
        self.ip_input = ""
        self.room_name_input = ""
        self.input_active = False
        self.room_name_active = False
        self.is_ready = False
        self.opponent_ready = False
        
        # 缓存常用文本渲染
        self.cached_texts = {
            'title': self.font.render("联机大厅", True, (255, 255, 255)),
            'create': self.font.render("创建房间", True, (255, 255, 255)),
            'join': self.font.render("加入房间", True, (255, 255, 255)),
            'ready': self.font.render("准备", True, (255, 255, 255)),
            'start': self.font.render("开始游戏", True, (255, 255, 255))
        }
        
        # 创建按钮（使用缓存的文本）
        self.buttons = {
            'create': Button("创建房间", 300, 150, font=self.font),
            'join': Button("加入房间", 300, 200, font=self.font),
            'ready': Button("准备", 300, 300, active=False, font=self.font),
            'start': Button("开始游戏", 300, 350, active=False, font=self.font)
        }
        
        # 创建输入框
        self.input_boxes = {
            'room_name': InputBox(300, 100, 200, 32, "房间名称", font=self.font),
            'ip': InputBox(300, 250, 200, 32, "输入IP地址", font=self.font)
        }
        
        self.error_message = ""
        self.error_timer = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # 处理按钮点击
            if self.buttons['create'].clicked(event.pos):
                if self.network.start_server():
                    self.buttons['ready'].active = True
                    self.buttons['create'].active = False
                    self.buttons['join'].active = False
                    
            elif self.buttons['join'].clicked(event.pos):
                if self.network.connect_to_server(self.ip_input):
                    self.buttons['ready'].active = True
                    self.buttons['create'].active = False
                    self.buttons['join'].active = False
                    
            elif self.buttons['ready'].clicked(event.pos):
                self.is_ready = not self.is_ready
                self.network.send_data({
                    'type': 'ready',
                    'value': self.is_ready
                })
                
        elif event.type == pygame.KEYDOWN:
            if self.input_active:
                if event.key == pygame.K_RETURN:
                    self.input_active = False
                elif event.key == pygame.K_BACKSPACE:
                    self.ip_input = self.ip_input[:-1]
                else:
                    self.ip_input += event.unicode
                    
    def update(self):
        # 更新输入框
        for box in self.input_boxes.values():
            box.update()
        
        # 更新错误消息计时器
        if self.error_timer > 0:
            self.error_timer -= 1

    def draw(self):
        # 绘制背景
        self.screen.fill((30, 30, 50))
        
        # 绘制标题
        title_rect = self.cached_texts['title'].get_rect(center=(400, 50))
        self.screen.blit(self.cached_texts['title'], title_rect)
        
        # 绘制按钮
        for button in self.buttons.values():
            button.draw(self.screen)
        
        # 绘制输入框
        for box in self.input_boxes.values():
            box.draw(self.screen)
        
        # 绘制错误信息
        if self.error_message and self.error_timer > 0:
            error_text = self.small_font.render(self.error_message, True, (255, 100, 100))
            error_rect = error_text.get_rect(center=(400, 500))
            self.screen.blit(error_text, error_rect)
        
        # 绘制准备状态
        if self.is_ready or self.opponent_ready:
            ready_text = self.small_font.render(
                f"我方: {'已准备' if self.is_ready else '未准备'} | "
                f"对方: {'已准备' if self.opponent_ready else '未准备'}",
                True, (100, 255, 100))
            ready_rect = ready_text.get_rect(center=(400, 400))
            self.screen.blit(ready_text, ready_rect)
        
        pygame.display.flip() 