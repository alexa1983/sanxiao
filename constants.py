from enum import Enum

class GameState(Enum):
    MENU = 0      # 菜单/大厅状态
    PLAYING = 1   # 游戏进行中
    PAUSED = 2    # 游戏暂停
    GAME_OVER = 3 # 游戏结束