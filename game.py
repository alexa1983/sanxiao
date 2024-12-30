import pygame
import random
import sys
import math
import os
from enum import Enum
from constants import GameState
from network_manager import NetworkManager
from network_lobby import NetworkLobby
from battle_platform import BattlePlatform

# 初始化 Pygame
pygame.init()

# 游戏常量
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
GRID_SIZE = 8
CELL_SIZE = 60
GRID_OFFSET_X = (WINDOW_WIDTH - GRID_SIZE * CELL_SIZE) // 2
GRID_OFFSET_Y = (WINDOW_HEIGHT - GRID_SIZE * CELL_SIZE) // 2

# 动画常量
ANIMATION_SPEED = 0.2
FADE_SPEED = 0.001
DROP_SPEED = 0.5  # 添加掉落速度常量

# 设置显示模式
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("魔法符文消除")

# 获取当前脚本的目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(SCRIPT_DIR, 'assets')

# 特殊符文类型
class SpecialType(Enum):
    NONE = 0
    EXPLOSIVE = 1  # 爆炸符文
    LINE = 2       # 直线符文
    MAGIC = 3      # 魔法球

# 定义宝石类型和对应的图片文件名
GEM_TYPES = {
    'FIRE': 'fire.png',
    'WATER': 'water.png',
    'WIND': 'wind.png',
    'EARTH': 'earth.png',
    'LIGHT': 'light.png',
    'SHADOW': 'shadow.png'
}

# 加载图片
def load_gem_images():
    images = {}
    for gem_type, image_file in GEM_TYPES.items():
        try:
            # 构建完整的图片路径
            image_path = os.path.join(ASSETS_DIR, image_file)
            print(f"尝试加载图片: {image_path}")
            
            # 加载图片
            image = pygame.image.load(image_path).convert_alpha()
            # 缩放到合适的大小
            image = pygame.transform.scale(image, (CELL_SIZE-4, CELL_SIZE-4))
            
            # 创建一个带有边距的surface
            final_surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            final_surface.blit(image, (2, 2))  # 在中心位置绘制图片
            
            images[gem_type] = final_surface
            print(f"成功加载图片: {gem_type}")
            
        except Exception as e:
            print(f"加载图片出错 {gem_type}: {e}")
            # 如果加载失败，创建一个彩色方块作为替代
            surface = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            color = (255, 0, 0) if gem_type == 'FIRE' else \
                   (0, 0, 255) if gem_type == 'WATER' else \
                   (0, 255, 0) if gem_type == 'WIND' else \
                   (139, 69, 19) if gem_type == 'EARTH' else \
                   (255, 255, 0) if gem_type == 'LIGHT' else \
                   (128, 0, 128)  # SHADOW
            pygame.draw.rect(surface, color + (255,), (0, 0, CELL_SIZE, CELL_SIZE))
            images[gem_type] = surface
            
    return images

# 加载所有宝石图片
GEM_IMAGES = load_gem_images()
GEM_TYPES = list(GEM_TYPES.keys())  # 转换为列表以便随机选择

class Gem:
    def __init__(self, type, row, col):
        self.type = type
        self.row = row
        self.col = col
        self.target_row = row
        self.target_col = col
        self.y = row * CELL_SIZE + GRID_OFFSET_Y
        self.x = col * CELL_SIZE + GRID_OFFSET_X
        self.alpha = 255
        self.scale = 1.0
        self.removing = False
        self.remove_timer = 1.0
        self.moving = False
        self.special_type = SpecialType.NONE
        self.special_effect_angle = 0  # 用于特效动画

    def update(self, dt):
        # 更新位置
        target_x = self.target_col * CELL_SIZE + GRID_OFFSET_X
        target_y = self.target_row * CELL_SIZE + GRID_OFFSET_Y
        
        dx = target_x - self.x
        dy = target_y - self.y
        
        if abs(dx) > 0.1 or abs(dy) > 0.1:
            self.moving = True
            self.x += dx * DROP_SPEED * dt * 60
            self.y += dy * DROP_SPEED * dt * 60
        else:
            self.moving = False
            self.x = target_x
            self.y = target_y

        # 更新特效动画
        self.special_effect_angle += dt * 2  # 旋转特效

        # 更新消除动画
        if self.removing:
            self.remove_timer -= dt
            progress = 1.0 - max(0, self.remove_timer)
            self.alpha = 255 * (1.0 - progress)
            self.scale = 1.0 - (progress * 0.5)
            return self.remove_timer <= 0
        return False

    def draw(self, screen):
        if self.alpha <= 0:
            return
            
        size = int(CELL_SIZE * self.scale)
        if size <= 0:
            return
            
        # 创建临时surface
        temp_surface = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # 获取并缩放宝石图片
        original_image = GEM_IMAGES[self.type]
        if size != CELL_SIZE:
            scaled_image = pygame.transform.scale(original_image, (size, size))
        else:
            scaled_image = original_image
        
        # 绘制宝石
        temp_surface.blit(scaled_image, (0, 0))
        
        # 为特殊符文添加特效
        if self.special_type != SpecialType.NONE:
            effect_surface = pygame.Surface((size, size), pygame.SRCALPHA)
            
            if self.special_type == SpecialType.EXPLOSIVE:
                # 爆炸符文效果：脉动的光环
                glow_size = abs(math.sin(self.special_effect_angle)) * 5 + size//2
                pygame.draw.circle(effect_surface, (255, 165, 0, 100), 
                                 (size//2, size//2), int(glow_size))
                
            elif self.special_type == SpecialType.LINE:
                # 直线符文效果：旋转的十字
                center = size // 2
                angle = self.special_effect_angle
                length = size // 2
                points = [
                    (center + math.cos(angle) * length, center + math.sin(angle) * length),
                    (center - math.cos(angle) * length, center - math.sin(angle) * length),
                    (center + math.cos(angle + math.pi/2) * length, center + math.sin(angle + math.pi/2) * length),
                    (center - math.cos(angle + math.pi/2) * length, center - math.sin(angle + math.pi/2) * length)
                ]
                for p1, p2 in [(points[0], points[1]), (points[2], points[3])]:
                    pygame.draw.line(effect_surface, (255, 215, 0, 150), p1, p2, 3)
                
            elif self.special_type == SpecialType.MAGIC:
                # 魔法球效果：旋转的星星
                center = size // 2
                points = []
                num_points = 5
                for i in range(num_points * 2):
                    angle = self.special_effect_angle + i * math.pi / num_points
                    radius = size // 3 if i % 2 == 0 else size // 6
                    x = center + math.cos(angle) * radius
                    y = center + math.sin(angle) * radius
                    points.append((x, y))
                pygame.draw.polygon(effect_surface, (255, 255, 255, 150), points)
            
            temp_surface.blit(effect_surface, (0, 0))
        
        # 应用透明度
        if self.alpha < 255:
            alpha_surface = pygame.Surface((size, size), pygame.SRCALPHA)
            alpha_surface.fill((255, 255, 255, int(self.alpha)))
            temp_surface.blit(alpha_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        # 绘制到屏幕
        draw_x = self.x + (CELL_SIZE - size) // 2
        draw_y = self.y + (CELL_SIZE - size) // 2
        screen.blit(temp_surface, (draw_x, draw_y))

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        
        # 设置显示
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("魔法符文消除")
        
        # 加载背景图片
        try:
            background_path = os.path.join(ASSETS_DIR, 'background.png')
            self.background = pygame.image.load(background_path).convert()
            self.background = pygame.transform.scale(self.background, (WINDOW_WIDTH, WINDOW_HEIGHT))
            print("背景图片加载成功")
        except Exception as e:
            print(f"背景图片加载失败: {e}")
            # 创建默认背景
            self.background = pygame.Surface(self.screen.get_size())
            self.background = self.background.convert()
            self.background.fill((30, 30, 50))
        
        # 加载背景音乐
        try:
            pygame.mixer.music.load(os.path.join(ASSETS_DIR, 'background_music.mp3'))
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
            print("背景音乐加载成功")
        except Exception as e:
            print(f"背景音乐加载失败: {e}")
        
        # 初始化字体
        try:
            # 尝试从assets目录加载自定义字体
            font_path = os.path.join('assets', 'simhei.ttf')
            if os.path.exists(font_path):
                self.font = pygame.font.Font(font_path, 20)
                self.small_font = pygame.font.Font(font_path, 20)
                print("Game: 使用自定义字体文件")
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
                        self.font = pygame.font.SysFont(font_name, 20)
                        self.small_font = pygame.font.SysFont(font_name, 20)
                        print(f"Game: 使用系统字体: {font_name}")
                        font_loaded = True
                        break
                    except:
                        continue
                
                if not font_loaded:
                    print("Game: 无法加载中文字体，使用默认字体")
                    self.font = pygame.font.Font(None, 20)
                    self.small_font = pygame.font.Font(None, 20)
        
        except Exception as e:
            print(f"Game: 字体加载错误: {e}")
            self.font = pygame.font.Font(None, 20)
            self.small_font = pygame.font.Font(None, 20)
        
        # 缓存主菜单文本
        self.menu_texts = {
            'single_player': self.font.render("单人游戏", True, (255, 255, 255)),
            'multiplayer': self.font.render("联机对战", True, (255, 255, 255)),
            'exit': self.font.render("退出游戏", True, (255, 255, 255))
        }
        
        # 初始化游戏状态
        self.game_state = GameState.MENU
        self.menu_state = "MAIN"
        
        # 初始化网络管理器和其他组件
        self.network = NetworkManager()
        self.network_lobby = NetworkLobby(self.screen, self.network)
        self.battle_platform = BattlePlatform(self.screen, self.network)
        
        self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.initialize_grid()
        
        self.selected = None
        self.score = 0
        self.moves = 30
        
        print("可用字体:", pygame.font.get_fonts())  # 打印系统所有可用字体
        
        self.clock = pygame.time.Clock()
        self.animating = False
        self.combo = 0
        self.max_combo = 0
        
        # 加载音效
        try:
            # 加载音效时添加错误处理
            self.click_sound = pygame.mixer.Sound(os.path.join('assets', 'click.wav'))
            self.eliminate_sound = pygame.mixer.Sound(os.path.join('assets', 'eliminate.wav'))
            self.special_sound = pygame.mixer.Sound(os.path.join('assets', 'special.wav'))
            
            # 测试音效是否正确加载
            print("音效加载成功")
        except Exception as e:
            print(f"加载音效时出错: {e}")
            # 如果加载失败，创建空的音效对象防止程序崩溃
            self.click_sound = None
            self.eliminate_sound = None
            self.special_sound = None
        
        # 设置音效音量
        if self.click_sound is not None:
            self.click_sound.set_volume(1.4)
        if self.eliminate_sound is not None:
            self.eliminate_sound.set_volume(1.6)
        if self.special_sound is not None:
            self.special_sound.set_volume(1.7)
        
        print("游戏初始化完成")
        print(f"当前游戏状态: {self.game_state}")
        print("网络大厅初始化完成")
        
        self.battle_platform = BattlePlatform(self.screen, self.network)

    def initialize_grid(self):
        while True:
            # 填充网格0
            for i in range(GRID_SIZE):
                for j in range(GRID_SIZE):
                    gem_type = random.choice(GEM_TYPES)
                    self.grid[i][j] = Gem(gem_type, i, j)
            
            # 检查是否有初始匹配
            matches, _ = self.find_matches()
            if not matches:
                break
            
            # 如果有匹配，清空网格重试
            self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    def draw(self):
        """绘制游戏界面"""
        try:
            # 绘制背景
            self.screen.blit(self.background, (0, 0))
            
            # 绘制半透明的游戏区域背景
            game_area = pygame.Surface((GRID_SIZE * CELL_SIZE + 20, GRID_SIZE * CELL_SIZE + 20))
            game_area.fill((30, 30, 50))
            game_area.set_alpha(180)
            self.screen.blit(game_area, 
                            (GRID_OFFSET_X - 10, GRID_OFFSET_Y - 10))
            
            # 绘制网格
            for i in range(GRID_SIZE):
                for j in range(GRID_SIZE):
                    x = j * CELL_SIZE + GRID_OFFSET_X
                    y = i * CELL_SIZE + GRID_OFFSET_Y
                    rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                    pygame.draw.rect(self.screen, (80, 80, 100), rect, 1)
                    
                    # 绘制宝石
                    if self.grid[i][j]:
                        self.grid[i][j].draw(self.screen)
                        # 为特殊符文添加闪光效果
                        if self.grid[i][j].special_type != SpecialType.NONE:
                            glow_color = (255, 255, 200, 
                                        int(abs(math.sin(pygame.time.get_ticks() * 0.005)) * 155 + 100))
                            s = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                            pygame.draw.rect(s, glow_color, (0, 0, CELL_SIZE, CELL_SIZE), 3)
                            self.screen.blit(s, (x, y))
            
            # 绘制选中效果
            if self.selected:
                i, j = self.selected
                x = j * CELL_SIZE + GRID_OFFSET_X
                y = i * CELL_SIZE + GRID_OFFSET_Y
                rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)
            
            # 创建半透明的状态显示背景
            status_bg_width = 160   # 修改宽度
            status_bg_height = 120  # 修改高度
            status_bg = pygame.Surface((status_bg_width, status_bg_height))
            status_bg.fill((30, 30, 50))
            status_bg.set_alpha(180)
            self.screen.blit(status_bg, (5, 5))
            
            # 绘制游戏状态信息
            y_offset = 10
            texts = [
                (f"分数: {self.score}", self.font),
                (f"剩余步数: {self.moves}", self.font),
                (f"当前连击: {self.combo}", self.small_font),
                (f"最大连击: {self.max_combo}", self.small_font)
            ]
            
            for text, font in texts:
                rendered_text = font.render(text, True, (255, 255, 255))
                self.screen.blit(rendered_text, (10, y_offset))
                y_offset += 28  # 进一步微调行间距
            
        except Exception as e:
            print(f"绘制错误: {e}")
            import traceback
            traceback.print_exc()

    def get_cell(self, pos):
        x, y = pos
        if (GRID_OFFSET_X <= x <= GRID_OFFSET_X + GRID_SIZE * CELL_SIZE and
            GRID_OFFSET_Y <= y <= GRID_OFFSET_Y + GRID_SIZE * CELL_SIZE):
            return ((y - GRID_OFFSET_Y) // CELL_SIZE,
                   (x - GRID_OFFSET_X) // CELL_SIZE)
        return None

    def find_matches(self):
        """查找匹配的宝石并返回特殊符文信息"""
        matches = set()
        special_matches = {}
        
        # 检查水平匹配
        for i in range(GRID_SIZE):
            j = 0
            while j < GRID_SIZE:
                if not self.grid[i][j]:
                    j += 1
                    continue
                    
                current_type = self.grid[i][j].type
                match_length = 1
                k = j + 1
                
                # 计算水平匹配长度
                while k < GRID_SIZE and self.grid[i][k] and self.grid[i][k].type == current_type:
                    match_length += 1
                    k += 1
                
                # 如果找到匹配
                if match_length >= 3:
                    match_positions = [(i, j+n) for n in range(match_length)]
                    matches.update(match_positions)
                    
                    # 根据匹配长度生成特殊符文
                    if match_length == 4:
                        special_matches[(i, j)] = SpecialType.EXPLOSIVE
                    elif match_length == 5:
                        special_matches[(i, j)] = SpecialType.LINE
                    elif match_length >= 6:
                        special_matches[(i, j)] = SpecialType.MAGIC
                
                j = k
        
        # 检查垂直匹配
        for j in range(GRID_SIZE):
            i = 0
            while i < GRID_SIZE:
                if not self.grid[i][j]:
                    i += 1
                    continue
                    
                current_type = self.grid[i][j].type
                match_length = 1
                k = i + 1
                
                # 计算垂直匹配长度
                while k < GRID_SIZE and self.grid[k][j] and self.grid[k][j].type == current_type:
                    match_length += 1
                    k += 1
                
                # 如果找到匹配
                if match_length >= 3:
                    match_positions = [(i+n, j) for n in range(match_length)]
                    matches.update(match_positions)
                    
                    # 根据匹配长度生成特殊符文
                    if match_length == 4:
                        special_matches[(i, j)] = SpecialType.EXPLOSIVE
                    elif match_length == 5:
                        special_matches[(i, j)] = SpecialType.LINE
                    elif match_length >= 6:
                        special_matches[(i, j)] = SpecialType.MAGIC
                
                i = k
        
        return matches, special_matches

    def remove_matches(self):
        """移除匹配的宝石并创建特效"""
        matches, special_matches = self.find_matches()
        if matches:
            print(f"找到匹配: {matches}")
            print(f"特殊符文: {special_matches}")
            
            # 增加连击计数和分数
            self.combo += 1
            self.max_combo = max(self.max_combo, self.combo)
            
            base_score = len(matches) * 10
            combo_bonus = self.combo * 5
            self.score += base_score + combo_bonus
            
            # 处理特殊符文的生成
            for pos, special_type in special_matches.items():
                i, j = pos
                if (i, j) in matches:  # 确保位置还在匹配集合中
                    matches.remove((i, j))  # 从普通匹配中移除
                    gem_type = self.grid[i][j].type
                    new_gem = Gem(gem_type, i, j)
                    new_gem.special_type = special_type
                    new_gem.target_row = i
                    new_gem.target_col = j
                    self.grid[i][j] = new_gem
                    print(f"生成特殊符文: 位置({i},{j}) 类型{special_type}")
                    
                    # 播放特殊符文生成音效
                    if self.special_sound:
                        self.special_sound.play()
            
            # 移除普通匹配
            for i, j in matches:
                if self.grid[i][j]:
                    self.grid[i][j].removing = True
                    self.grid[i][j].remove_timer = 1.0
                    print(f"移除普通宝石: ({i},{j})")
            
            # 播放消除音效
            if self.eliminate_sound:
                self.eliminate_sound.play()
            
            self.animating = True
            return True
        else:
            self.combo = 0  # 重置连击
            return False

    def activate_special_gem(self, row, col, special_type):
        """激活特殊符文效果"""
        try:
            affected_gems = set()
            print(f"开始激活特殊符文: 位置({row},{col}) 类型{special_type}")
            
            if special_type == SpecialType.EXPLOSIVE:
                # 爆炸效果：影响3x3范围
                for i in range(max(0, row-1), min(GRID_SIZE, row+2)):
                    for j in range(max(0, col-1), min(GRID_SIZE, col+2)):
                        if self.grid[i][j]:
                            affected_gems.add((i, j))
                            print(f"爆炸效果影响: ({i},{j})")
                    
            elif special_type == SpecialType.LINE:
                # 直线效果：清除整行和整列
                for i in range(GRID_SIZE):
                    if self.grid[i][col]:
                        affected_gems.add((i, col))
                    for j in range(GRID_SIZE):
                        if self.grid[row][j]:
                            affected_gems.add((row, j))
                    print(f"直线效果影响: {len(affected_gems)}个宝石")
                
            elif special_type == SpecialType.MAGIC:
                # 魔法效果：清除所有同类型的宝石
                target_type = self.grid[row][col].type
                for i in range(GRID_SIZE):
                    for j in range(GRID_SIZE):
                        if self.grid[i][j] and self.grid[i][j].type == target_type:
                            affected_gems.add((i, j))
                    print(f"魔法效果影响: {len(affected_gems)}个宝石")
            
            if affected_gems:
                # 移除受影响的宝石
                for i, j in affected_gems:
                    if self.grid[i][j]:
                        self.grid[i][j].removing = True
                        self.grid[i][j].remove_timer = 1.0
                        print(f"标记移除宝石: ({i},{j})")
                
                # 播放特殊效果音效
                if self.special_sound:
                    self.special_sound.play()
                
                # 设置动画状态
                self.animating = True
                
                print(f"特殊符文效果完成，影响了{len(affected_gems)}个宝石")
                return True
            
            return False
            
        except Exception as e:
            print(f"激活特殊符文错误: {e}")
            import traceback
            traceback.print_exc()
            return False

    def fill_empty(self):
        """填充空位并使宝石下落"""
        # 标记所有需要下落的宝石
        falling_gems = []
        
        # 从下往上检查每一列
        for j in range(GRID_SIZE):
            empty_count = 0
            for i in range(GRID_SIZE-1, -1, -1):
                if self.grid[i][j] is None:
                    empty_count += 1
                elif empty_count > 0:
                    # 如果上方有宝石且下方有空位，让宝石下落
                    gem = self.grid[i][j]
                    gem.target_row = i + empty_count
                    self.grid[i+empty_count][j] = gem
                    self.grid[i][j] = None
                    falling_gems.append(gem)
            
            # 在顶部添加新的宝石
            for i in range(empty_count):
                gem_type = random.choice(GEM_TYPES)
                new_gem = Gem(gem_type, -empty_count+i, j)
                new_gem.target_row = i
                self.grid[i][j] = new_gem
                falling_gems.append(new_gem)
        
        # 立即更新所有下落的宝石位置
        for gem in falling_gems:
            gem.moving = True

    def is_animating(self):
        """检查是否有动画正在播放"""
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                if self.grid[i][j] and (self.grid[i][j].removing or self.grid[i][j].moving):
                    return True
        return False

    def update_animations(self, dt):
        """更新所有动画效果"""
        try:
            any_removed = False
            
            # 更新所有宝石的动画
            for i in range(GRID_SIZE):
                for j in range(GRID_SIZE):
                    if self.grid[i][j]:
                        if self.grid[i][j].removing:
                            if self.grid[i][j].update(dt):
                                print(f"移除宝石: ({i},{j})")
                                self.grid[i][j] = None
                                any_removed = True
                        else:
                            self.grid[i][j].update(dt)
            
            # 如果有宝石被移除，立即触发填充
            if any_removed:
                print("检测到宝石移除，触发填充")
                self.fill_empty()
            
            return any_removed
            
        except Exception as e:
            print(f"更新动画错误: {e}")
            import traceback
            traceback.print_exc()
            return False

    def update_gem_positions(self, dt):
        """更新所有宝石的位置"""
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                if self.grid[i][j]:
                    self.grid[i][j].update(dt)
                    
                    # 如果宝石到达目标位置，更新其实际位置
                    target_x = self.grid[i][j].target_col * CELL_SIZE + GRID_OFFSET_X
                    target_y = self.grid[i][j].target_row * CELL_SIZE + GRID_OFFSET_Y
                    
                    if (abs(self.grid[i][j].x - target_x) < 1 and 
                        abs(self.grid[i][j].y - target_y) < 1):
                        self.grid[i][j].x = target_x
                        self.grid[i][j].y = target_y

    def run(self):
        running = True
        last_time = pygame.time.get_ticks()
        
        while running:
            current_time = pygame.time.get_ticks()
            dt = (current_time - last_time) / 1000.0
            last_time = current_time
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
                # 根据游戏状态和菜单状态处理事件
                if self.game_state == GameState.MENU:
                    if self.menu_state == "MAIN":
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            # 检查主菜单按钮点击
                            mouse_pos = event.pos
                            button_height = 50
                            spacing = 20
                            menu_items = [
                                ("单人游戏", lambda: self.start_single_player()),
                                ("联机对战", lambda: setattr(self, 'menu_state', "BATTLE")),
                                ("退出游戏", sys.exit)
                            ]
                            
                            start_y = (WINDOW_HEIGHT - (len(menu_items) * (button_height + spacing) - spacing)) // 2
                            
                            for i, (_, action) in enumerate(menu_items):
                                button_rect = pygame.Rect(
                                    (WINDOW_WIDTH - 200) // 2,
                                    start_y + i * (button_height + spacing),
                                    200,
                                    button_height
                                )
                                if button_rect.collidepoint(mouse_pos):
                                    action()
                                    break
                                    
                    elif self.menu_state == "LOBBY":
                        self.network_lobby.handle_event(event)
                    elif self.menu_state == "BATTLE":
                        self.battle_platform.handle_event(event)
                    
                elif self.game_state == GameState.PLAYING:
                    self.handle_game_event(event)
            
            # 根据游戏状态和菜单状态更新和绘制
            if self.game_state == GameState.MENU:
                if self.menu_state == "MAIN":
                    self.draw_main_menu()
                elif self.menu_state == "LOBBY":
                    self.network_lobby.update()
                    self.network_lobby.draw()
                elif self.menu_state == "BATTLE":
                    self.battle_platform.draw()
            elif self.game_state == GameState.PLAYING:
                self.update(dt)
                self.draw()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

    def draw_main_menu(self):
        """绘制主菜单"""
        self.screen.fill((30, 30, 50))
        
        menu_items = [
            (self.menu_texts['single_player'], lambda: setattr(self, 'game_state', GameState.PLAYING)),
            (self.menu_texts['multiplayer'], lambda: setattr(self, 'menu_state', "BATTLE")),
            (self.menu_texts['exit'], sys.exit)
        ]
        
        button_height = 50
        spacing = 20
        total_height = len(menu_items) * (button_height + spacing) - spacing
        start_y = (WINDOW_HEIGHT - total_height) // 2
        
        for i, (text_surface, _) in enumerate(menu_items):
            button_rect = pygame.Rect(
                (WINDOW_WIDTH - 200) // 2,
                start_y + i * (button_height + spacing),
                200,
                button_height
            )
            
            # 绘制按钮背景
            pygame.draw.rect(self.screen, (100, 100, 100), button_rect)
            pygame.draw.rect(self.screen, (200, 200, 200), button_rect, 2)
            
            # 绘制预渲染的文本
            text_rect = text_surface.get_rect(center=button_rect.center)
            self.screen.blit(text_surface, text_rect)

    def check_online_button_click(self, pos):
        """检查联机按钮是否被点击"""
        button_rect = pygame.Rect(
            (WINDOW_WIDTH - 200) // 2,
            (WINDOW_HEIGHT - 50) // 2 + 70,  # 调整位置到第二个按钮
            200,
            50
        )
        return button_rect.collidepoint(pos)

    def handle_game_event(self, event):
        """处理游戏事件"""
        try:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not self.animating:
                    cell = self.get_cell(event.pos)
                    if cell:
                        row, col = cell
                        current_gem = self.grid[row][col]
                        
                        # 检查是否点击了特殊符文
                        if current_gem and current_gem.special_type != SpecialType.NONE:
                            print(f"点击特殊符文: 位置({row},{col}) 类型{current_gem.special_type}")
                            if self.activate_special_gem(row, col, current_gem.special_type):
                                self.moves -= 1
                                # 播放点击音效
                                if self.click_sound:
                                    self.click_sound.play()
                            return
                        
                        # 普通宝石的选择和交换逻辑
                        if self.selected:
                            # 如果已经选中了一个宝石
                            selected_row, selected_col = self.selected
                            if abs(row - selected_row) + abs(col - selected_col) == 1:
                                # 相邻的宝石，尝试交换
                                self.swap_gems(selected_row, selected_col, row, col)
                            self.selected = None
                        else:
                            # 选择宝石
                            self.selected = (row, col)
                            # 播放点击音效
                            if self.click_sound:
                                self.click_sound.play()
                            
        except Exception as e:
            print(f"事件处理错误: {e}")
            import traceback
            traceback.print_exc()

    def start_single_player(self):
        """启动单人游戏"""
        print("Starting single player game...")
        try:
            self.game_state = GameState.PLAYING
            self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
            self.initialize_grid()
            self.selected = None
            self.score = 0
            self.moves = 30
            self.combo = 0
            self.max_combo = 0
            self.animating = False
            print("游戏初始化完成")
        except Exception as e:
            print(f"游戏初始化错误: {e}")

    def update(self, dt):
        """更新游戏状态"""
        try:
            if self.game_state == GameState.PLAYING:
                # 更新动画
                if self.animating:
                    any_removed = self.update_animations(dt)
                    if any_removed:
                        self.fill_empty()
                        # 立即更新所有宝石的位置
                        self.update_gem_positions(dt)
                    elif not self.is_animating():
                        self.animating = False
                        if not self.remove_matches():
                            if self.moves <= 0:
                                print("游戏结束")
                                self.game_state = GameState.MENU
                                self.menu_state = "MAIN"
                
                # 更新宝石状态
                self.update_gem_positions(dt)
                
                # 检查是否需要填充空位
                if not self.animating and not self.is_animating():
                    matches = self.find_matches()[0]
                    if matches:
                        self.animating = True
                        self.remove_matches()
        except Exception as e:
            print(f"更新错误: {e}")
            import traceback
            traceback.print_exc()

    def swap_gems(self, row1, col1, row2, col2):
        """交换两个宝石"""
        try:
            print(f"尝试交换宝石: ({row1},{col1}) <-> ({row2},{col2})")
            gem1 = self.grid[row1][col1]
            gem2 = self.grid[row2][col2]
            
            if not gem1 or not gem2:
                print("无效的交换：存在空宝石")
                return

            # 先执行交换
            self.grid[row1][col1] = gem2
            self.grid[row2][col2] = gem1
            gem1.target_row, gem1.target_col = row2, col2
            gem2.target_row, gem2.target_col = row1, col1

            # 检查是否形成匹配
            matches = self.find_matches()[0]
            if matches:
                print(f"形成新的匹配: {matches}")
                self.moves -= 1
                self.animating = True
                if self.eliminate_sound:
                    self.eliminate_sound.play()
                return True
            else:
                print("未形成匹配，恢复交换")
                # 恢复原位
                self.grid[row1][col1] = gem1
                self.grid[row2][col2] = gem2
                gem1.target_row, gem1.target_col = row1, col1
                gem2.target_row, gem2.target_col = row2, col2
                return False
            
        except Exception as e:
            print(f"交换宝石错误: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    game = Game()
    game.run()  