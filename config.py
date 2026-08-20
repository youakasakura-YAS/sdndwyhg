# Copyright (c) 2026 youakasakura‑YAS
# SPDX‑License‑Identifier: MIT
# Note: System architecture and module design conceived by human.
# Code assisted by AI, manually modified, debugged and integrated by human.

import pygame
import sys
import os

# ========== 窗口参数 ==========
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
FPS = 60

# ========== 摄像头参数 ==========
CAMERA_COUNT = 6
CAMERA_NAMES = ["银月之庭", "沐光之台", "霜月之子", "蛋卷工坊", "那夏镇", "那夏镇外滩"]

# ========== 地点路径名称 ==========
PATH_NAMES = CAMERA_NAMES + ["旗舰", "桑多涅的房间"]
PATH_INDEX = {name: i for i, name in enumerate(PATH_NAMES)}
PLAYER_ROOM_INDEX = PATH_INDEX["桑多涅的房间"]   
FLAGSHIP_INDEX = PATH_INDEX["旗舰"]          

# 地点映射
LOC_NAME_MAP = {i: name for i, name in enumerate(PATH_NAMES)}

# ========== 道路可通行关系 ==========
PATH_GRAPH = {
    "银月之庭": ["沐光之台", "霜月之子"],
    "沐光之台": ["银月之庭", "霜月之子", "蛋卷工坊"],
    "霜月之子": ["银月之庭", "沐光之台", "蛋卷工坊"],
    "蛋卷工坊": ["沐光之台", "霜月之子", "那夏镇", "那夏镇外滩"],
    "那夏镇": ["蛋卷工坊", "那夏镇外滩", "旗舰"],
    "那夏镇外滩": ["蛋卷工坊", "那夏镇", "旗舰"],
    "旗舰": ["那夏镇", "那夏镇外滩", "桑多涅的房间"],
    "桑多涅的房间": ["旗舰"],
}

# ========== 图片缩放系数 ==========
MONSTER_SCALE_MONITOR = 1.5
MONSTER_SCALE_ROOM = 1.2

# ========== 多生物绘制参数 ==========
MONSTER_MAX_IN_CHANNEL = 5  # 房间最大生物数
MONSTER_HORIZONTAL_OFFSET_RATIO = 0.75  # 横向偏移比例

# ========== 颜色参数 ==========
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY = (80, 80, 80)
COLOR_RED = (220, 30, 30)
COLOR_BLUE_LIGHT = (200, 200, 255)
COLOR_GRAY_LIGHT = (160, 160, 160)
COLOR_GREEN_SAFE = (60, 220, 60)
COLOR_YELLOW_WARN = (220, 180, 30)

# ========== 哥伦比娅AI参数 ==========
ROOM_STAY_MIN = 9
ROOM_STAY_MAX = 18
ROOM_GRACE_TIME = 3000
BACKSTEP_TIMES = 3
COLUMBIA_BASE_CD_MIN = 7000    # 冷却下限
COLUMBIA_BASE_CD_MAX = 15000   # 冷却上限
COLUMBIA_MIN_CD = 6000         # 加强冷却下限
COLUMBIA_DOUBLE_STEP_START_NIGHT = 3  # 两步走的夜数
COLUMBIA_DOUBLE_STEP_BASE = 0.1       # 基础两步走概率
COLUMBIA_DOUBLE_STEP_INCREMENT = 0.03 # 增加概率
COLUMBIA_DOUBLE_STEP_MAX = 0.5        # 概率上限

# ========== 努昂诺塔AI参数 ==========
NANT_BASE_CD_MIN = 9000    # 冷却下限
NANT_BASE_CD_MAX = 15000   # 冷却上限
NANT_MIN_CD = 7000         # 加强冷却下限
NANT_BASE_DOUBLE_STEP = 0.1  # 两步概率
NANT_MAX_DOUBLE_STEP = 0.6   # 两步概率上限
NANT_ROOM_GRACE = 3000       # 时间宽限
NANT_BACKWARD_IN_ROOM = 0.9 # 后退概率
NANT_FORWARD_IN_ROOM = 0.1  # 前进概率

# ========== 门维修参数 ==========
DOOR_REPAIR_TIME = 6000       

# ========== 一夜时长 ============
NIGHT_DURATION_MS = 7 * 60 * 1000

# ========== 隐蔽罩参数 ==========
COVER_MAX_TIME_MS = 23000
COVER_COOLDOWN_MS = 5000


# ========== 资源 ==========
# 函数部分
def get_internal_base():
    if getattr(sys, 'frozen', False) and hasattr(sys, "_MEIPASS"):
        return os.path.abspath(sys._MEIPASS)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def get_exe_root():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
    else:
        return os.path.dirname(os.path.abspath(__file__))

INTERNAL_BASE = get_internal_base()   
EXE_ROOT = get_exe_root()             

PHOTOS_ROOT = os.path.join(EXE_ROOT, "photos")
MUSIC_ROOT = os.path.join(EXE_ROOT, "music")

# ========== 路径组装 ======
# 图片部分
COVER_IMG_PATH = os.path.join(PHOTOS_ROOT, "YJLYBZ.png")
YYZT_BG_PATH = os.path.join(PHOTOS_ROOT, "YYZT.png")
MGZT_BG_PATH = os.path.join(PHOTOS_ROOT, "MGZT.png")          
SYZZ_BG_PATH = os.path.join(PHOTOS_ROOT, "SYZZ.png")          
NXZ_BG_PATH = os.path.join(PHOTOS_ROOT, "NXZ.png")            
NXZWT_BG_PATH = os.path.join(PHOTOS_ROOT, "NXZWT.png")        
DJGF_BG_PATH = os.path.join(PHOTOS_ROOT, "DLKLDJGF.png")      
WJFJ_BG_PATH = os.path.join(PHOTOS_ROOT, "SDNDFJ.png")
MENU_BG_PATH = os.path.join(PHOTOS_ROOT, "ZJM.png")
WJFJ_CLOSED_BG_PATH = os.path.join(PHOTOS_ROOT, "SDNDFJ-CD.png")
# 哥伦比娅和努昂诺塔图片
NANT_IMG_PATH = os.path.join(PHOTOS_ROOT, "NANT.png")
MONSTER_IMG_PATH = os.path.join(PHOTOS_ROOT, "GLBY.png")
# 哥伦比娅音效
SOUND_CLICK_PATH = os.path.join(MUSIC_ROOT, "columnbina", "CLK.wav")
JRFJ_SOUND_PATH = os.path.join(MUSIC_ROOT, "columnbina", "JRFJ.wav")
CLK_SOUND_PATH = os.path.join(MUSIC_ROOT, "columnbina", "CLK.wav")
CLK3_SOUND_PATH = os.path.join(MUSIC_ROOT, "columnbina", "LK-3.wav") # 进房间次数>3后使用的音频文件
BZD_SOUND_PATH = os.path.join(MUSIC_ROOT, "columnbina", "BZD.wav")

# 背景音乐
BG_MUSIC_PATH = os.path.join(MUSIC_ROOT, "BJYY.ogg")
CURRENT_HUM_PATH = os.path.join(MUSIC_ROOT, "JKYY.wav")  # 监控背景声（disable）

# ========== 监控UI常量 ==========
UI_BOX_WIDTH = 120          # 宽度
UI_BOX_HEIGHT = 60          # 高度
UI_BOX_SPACING = 10         # 框间距
UI_LINE_WIDTH = 3           # 连线粗细

# ========== 监控背景声音量 ==========
CURRENT_VOLUME = 0.3

# ========== 状态常量 ==========
STATE_WANDER = 0
STATE_IN_ROOM = 2

# ========== 通用缩放裁剪函数 ==========
def scale_and_crop(surf, target_w, target_h):
    src_w, src_h = surf.get_size()
    scale = max(target_w / src_w, target_h / src_h)
    new_w = int(src_w * scale)
    new_h = int(src_h * scale)
    scaled = pygame.transform.smoothscale(surf, (new_w, new_h))
    crop_x = (new_w - target_w) // 2
    crop_y = (new_h - target_h) // 2
    return scaled.subsurface(pygame.Rect(crop_x, crop_y, target_w, target_h))

# ========== UI控制 ==========
SHOW_CONTROL_HINT = True

# ========== 监控UI地图坐标 ==========
UI_MAP_POSITIONS = {
    "银月之庭": (1740, 490),
    "沐光之台": (1580, 580),
    "霜月之子": (1740, 580),
    "蛋卷工坊": (1740, 670),
    "那夏镇": (1740, 760),
    "那夏镇外滩": (1580, 760),
    "旗舰": (1740, 850),
    "桑多涅的房间": (1740, 940),
}

# 连线
UI_MAP_LINES = [
    ("银月之庭", "沐光之台"),
    ("银月之庭", "霜月之子"),
    ("沐光之台", "霜月之子"),
    ("沐光之台", "蛋卷工坊"),
    ("霜月之子", "蛋卷工坊"),
    ("蛋卷工坊", "那夏镇"),
    ("蛋卷工坊", "那夏镇外滩"),
    ("那夏镇", "那夏镇外滩"),
    ("那夏镇", "旗舰"),
    ("那夏镇外滩", "旗舰"),
    ("旗舰", "桑多涅的房间"),
]