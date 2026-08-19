# Copyright (c) 2026 youakasakura‑YAS
# SPDX‑License‑Identifier: MIT
# Note: System architecture and module design conceived by human.
# Code assisted by AI, manually modified, debugged and integrated by human.
import pygame
import sys
import json
import os
from datetime import datetime
from config import *
from core.camera_sys import CameraSystem
from core.power_sys import PowerSystem
from core.player_cover import CoverSystem
from core.columbia import Columbia
from core.nuantanota import Nuantanota
from config import scale_and_crop  # 缩放函数

# ===================== 路径处理 =====================
BASE_DIR = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
if hasattr(sys, "_MEIPASS"):
    BASE_DIR = sys._MEIPASS
KEY_FILE = os.path.join(BASE_DIR, "S1O0.json")
LOG_FOLDER = os.path.join(BASE_DIR, "log")
REAL_KEY = "kZ5W3XSrF5FMpcx2wjZwwVKFKCtFENpSS8CyFc26H8vcQSYpkFxMkdAV64Zf6HSW"

if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)
time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOG_FILE_PATH = os.path.join(LOG_FOLDER, f"{time_str}.log")
game_log_buffer = []

def check_debug_key() -> bool:
    if not os.path.exists(KEY_FILE):
        return False
    try:
        with open(KEY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("key", "") == REAL_KEY
    except Exception:
        return False

def write_all_log():
    if len(game_log_buffer) == 0:
        return
    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write("===== 本局游戏记录开始 =====\n")
            for line in game_log_buffer:
                f.write(line + "\n")
            f.write("===== 本局游戏记录结束 =====\n\n")
        print(f"日志已保存至：{LOG_FILE_PATH}")
    except Exception as e:
        print("日志写入失败：", e)
    game_log_buffer.clear()

def cleanup_logs(max_count=10):
    if not os.path.exists(LOG_FOLDER):
        return
    try:
        files = [os.path.join(LOG_FOLDER, f) for f in os.listdir(LOG_FOLDER) if f.endswith('.log')]
        if len(files) <= max_count:
            return
        # 按修改时间排序
        files.sort(key=os.path.getmtime)
        for old_file in files[:-max_count]:
            os.remove(old_file)
    except Exception as e:
        print("清理旧日志失败：", e)

def get_font(size):
    font_path = os.path.join(BASE_DIR,"sdndwyhg.ttf")
    if os.path.exists(font_path):
        try:
            return pygame.font.Font(font_path, size)
        except Exception:
            print(f"字体加载失败:{e}")
            pass
    try:
        return pygame.font.SysFont("simhei", size)
    except:
        try:
            return pygame.font.SysFont("microsoft yahei", size)
        except:
            return pygame.font.SysFont("arial", size)

# ===================== pygame初始化 =====================
pygame.init()
cleanup_logs()
pygame.mixer.init()
pygame.key.stop_text_input()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
pygame.display.set_caption("桑多涅的五夜后宫")
clock = pygame.time.Clock()
font = get_font(26)
font_big = get_font(36)
font_ui = get_font(20)
font_popup = get_font(40)
FPS = 60

# ===================== 资源加载 =====================


menu_bg = None
try:
    menu_raw = pygame.image.load(MENU_BG_PATH).convert()
    menu_bg = scale_and_crop(menu_raw, SCREEN_WIDTH, SCREEN_HEIGHT)
except Exception as e:
    print("菜单背景加载失败：", e)

# 玩家房间背景
player_room_open_bg = None
player_room_closed_bg = None
try:
    pr_raw_open = pygame.image.load(WJFJ_BG_PATH).convert()
    player_room_open_bg = scale_and_crop(pr_raw_open, SCREEN_WIDTH, SCREEN_HEIGHT)
except Exception as e:
    print("房间开门背景加载失败：", e)

try:
    pr_raw_closed = pygame.image.load(WJFJ_CLOSED_BG_PATH).convert()
    player_room_closed_bg = scale_and_crop(pr_raw_closed, SCREEN_WIDTH, SCREEN_HEIGHT)
except Exception as e:
    print("房间关门背景加载失败：", e)

# 监控背景贴图
monitor_bg_list = [None] * 6
bg_paths = [YYZT_BG_PATH, MGZT_BG_PATH, SYZZ_BG_PATH, DJGF_BG_PATH, NXZ_BG_PATH, NXZWT_BG_PATH]
for i, path in enumerate(bg_paths):
    try:
        raw = pygame.image.load(path).convert()
        monitor_bg_list[i] = raw
    except Exception as e:
        print(f"监控背景{i}加载失败：", e)

# ========== 电流音效和跳脸贴图（disable） ==========
current_hum_sound = None
jumpscare_img = None

def load_additional_assets():
    global current_hum_sound, jumpscare_img
    try:
        current_hum_sound = pygame.mixer.Sound(CURRENT_HUM_PATH)
        current_hum_sound.set_volume(CURRENT_VOLUME)
    except Exception as e:
        print("监控背景声加载失败", e)
    try:
        jumpscare_img = pygame.image.load("photos/JUMPSCARE.png").convert_alpha()
        jumpscare_img = pygame.transform.scale(jumpscare_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
    except Exception as e:
        print("跳脸贴图加载失败", e)

load_additional_assets()

# ===================== 全局状态 =====================
SCENE_MENU = 0
SCENE_GAME = 1
SCENE_GAMEOVER = 2
SCENE_VICTORY = 3
SCENE_PAUSE = 4

current_scene = SCENE_MENU
game_mode = 0
current_night = 1
power = None
camera = None
cover = None
columbia = None
nant = None
night_timer = 0
show_debug = False
can_open_debug = check_debug_key()
is_paused = False
SHOW_CONTROL_HINT = True
door_open = True  
is_repairing = False      
repair_progress = 0  
door_broken = False

# 跳脸相关全局变量
jumpscare_active = False
jumpscare_start_time = 0
jumpscare_fade_start = 0
jumpscare_fade_alpha = 255

# 提示相关变量
popup_text = ""
popup_timer = 0
# 旗舰提示文字
FLAGSHIP_HINTS = [
    "监控无法连接",
    "监控好像被破坏了",
    "监控可能不存在",
    "NameError: name is not defined",
    "未知的监控",
    "监控不见了喵"
]
# 桑多涅的房间提示文字
PLAYER_ROOM_HINTS = [
    "NameError: name is not defined",
    "未知的监控",
    "你自己看还不够么？",
    "其实你看的见吧。",
    "监控不见了喵"
]

# ===================== 游戏初始化 =====================
def init_game_scene():
    global power, camera, cover, columbia, nant, night_timer, is_paused, door_open, door_broken
    global jumpscare_active, jumpscare_start_time, jumpscare_fade_alpha
    game_log_buffer.clear()
    power = PowerSystem()
    camera = CameraSystem()
    cover = CoverSystem()
    columbia = Columbia()
    nant = Nuantanota()
    nant.reset(current_night)
    night_timer = 0
    is_paused = False
    door_open = True 
    door_broken = False 
    jumpscare_active = False
    jumpscare_start_time = 0
    jumpscare_fade_alpha = 255
    try:
        pygame.mixer.music.load(BG_MUSIC_PATH)
        pygame.mixer.music.set_volume(0.6)
        pygame.mixer.music.play(-1)
    except Exception as e:
        print("背景音乐加载失败：", e)

def time_to_clock(ms):
    progress = ms / NIGHT_DURATION_MS
    total_min = progress * 360
    h = int(total_min // 60)
    m = int(total_min % 60)
    return f"{h:02d}:{m:02d}"

# ===================== 跳脸管理 =====================
def update_jumpscare():
    global jumpscare_active, jumpscare_start_time, jumpscare_fade_alpha, current_scene
    if not jumpscare_active:
        return
    now = pygame.time.get_ticks()
    elapsed = now - jumpscare_start_time
    if elapsed < 2000:
        jumpscare_fade_alpha = 255
    elif elapsed < 2400:
        progress = (elapsed - 2000) / 400.0
        jumpscare_fade_alpha = int(255 * (1 - progress))
    else:
        jumpscare_active = False
        write_all_log()
        current_scene = SCENE_GAMEOVER

# ===================== 监控背景音控制 =====================
def update_current_hum():
    if current_hum_sound is None:
        return
    if camera.open and not power.is_outage:
        if not hasattr(update_current_hum, "is_playing"):
            update_current_hum.is_playing = False
        if not update_current_hum.is_playing:
            current_hum_sound.play(-1)
            update_current_hum.is_playing = True
    else:
        if hasattr(update_current_hum, "is_playing") and update_current_hum.is_playing:
            current_hum_sound.stop()
            update_current_hum.is_playing = False

# ===================== 监控绘制 =====================
def calc_monster_positions(monster_list, area_w, area_h, inner_pad):
    count = len(monster_list)
    if count == 0:
        return []

    positions = []
    center_x = (area_w - monster_list[0][1]) // 2
    base_y = area_h - monster_list[0][2] - 10
    offset = int(monster_list[0][1] * MONSTER_HORIZONTAL_OFFSET_RATIO)

    if count == 1:
        positions.append((center_x, base_y, 0))
    elif count == 2:
        positions.append((center_x - offset, base_y, 0))
        positions.append((center_x + offset, base_y, 1))
    elif count == 3:
        positions.append((center_x - offset, base_y, 0))
        positions.append((center_x, base_y, 1))
        positions.append((center_x + offset, base_y, 2))
    elif count == 4:
        positions.append((center_x - offset, base_y, 0))
        positions.append((center_x + offset, base_y, 1))
        positions.append((center_x, base_y, 2))
        mid_left = (center_x - offset + center_x) // 2
        positions.append((mid_left, base_y - 5, 3))
    elif count >= 5:
        positions.append((center_x - offset, base_y, 0))
        positions.append((center_x + offset, base_y, 1))
        positions.append((center_x, base_y, 2))
        mid_left = (center_x - offset + center_x) // 2
        mid_right = (center_x + offset + center_x) // 2
        positions.append((mid_left, base_y - 5, 3))
        positions.append((mid_right, base_y - 5, 4))

    result = []
    for i, (x, y, layer) in enumerate(positions):
        result.append((x + inner_pad, y + inner_pad, layer, monster_list[i][0]))
    result.sort(key=lambda item: item[2])
    return result

def draw_monitor_fullscreen():
    # 背景
    bg_surf = monitor_bg_list[camera.current]
    if bg_surf is not None:
        try:
            full_bg = pygame.transform.smoothscale(bg_surf, (SCREEN_WIDTH, SCREEN_HEIGHT))
            screen.blit(full_bg, (0, 0))
        except:
            screen.fill((20, 20, 30))
    else:
        screen.fill((20, 20, 30))

    # 怪物
    channel_monsters = []
    if columbia.path_val == camera.current:
        channel_monsters.append(("col", columbia.monster_w, columbia.monster_h))
    if nant.path_val == camera.current:
        channel_monsters.append(("nant", nant.monster_w, nant.monster_h))
    if channel_monsters:
        positions = calc_monster_positions(channel_monsters, SCREEN_WIDTH, SCREEN_HEIGHT, 0)
        for x, y, layer, m_id in positions:
            if m_id == "col":
                columbia.draw_in_monitor(screen, x, y)
            elif m_id == "nant":
                nant.draw_in_monitor(screen, x, y)

    # 监控 UI
    draw_monitor_ui()

def draw_monitor_ui():
    draw_monitor_ui.ui_rects = []

    # 连线
    for name1, name2 in UI_MAP_LINES:
        if name1 not in UI_MAP_POSITIONS or name2 not in UI_MAP_POSITIONS:
            continue
        x1, y1 = UI_MAP_POSITIONS[name1]
        x2, y2 = UI_MAP_POSITIONS[name2]
        rect1 = pygame.Rect(x1, y1, UI_BOX_WIDTH, UI_BOX_HEIGHT)
        rect2 = pygame.Rect(x2, y2, UI_BOX_WIDTH, UI_BOX_HEIGHT)

        cx1, cy1 = rect1.center
        cx2, cy2 = rect2.center
        dx = cx2 - cx1
        dy = cy2 - cy1

        if abs(dx) >= abs(dy):
            if cx1 < cx2:
                start = (rect1.right, rect1.centery)
                end   = (rect2.left,  rect2.centery)
            else:
                start = (rect2.right, rect2.centery)
                end   = (rect1.left,  rect1.centery)
        else:
            if cy1 < cy2:
                start = (rect1.centerx, rect1.bottom)
                end   = (rect2.centerx, rect2.top)
            else:
                start = (rect2.centerx, rect2.bottom)
                end   = (rect1.centerx, rect1.top)

        pygame.draw.line(screen, (255, 255, 255), start, end, UI_LINE_WIDTH)

    # 地点框
    for name, (x, y) in UI_MAP_POSITIONS.items():
        rect = pygame.Rect(x, y, UI_BOX_WIDTH, UI_BOX_HEIGHT)
        if name == "旗舰":
            border_color = (180, 180, 180)
        elif name == "桑多涅的房间":
            border_color = (200, 100, 100)
        else:
            border_color = (255, 255, 255)
        pygame.draw.rect(screen, border_color, rect, 2)
        text_surf = font_ui.render(name, True, border_color)
        text_rect = text_surf.get_rect(center=rect.center)
        screen.blit(text_surf, text_rect)
        draw_monitor_ui.ui_rects.append((name, rect))
        
def handle_monitor_click(mx, my):
    global popup_text, popup_timer
    if not camera.open or power.is_outage:
        return
    if not hasattr(draw_monitor_ui, "ui_rects") or not draw_monitor_ui.ui_rects:
        return
    for name, rect in draw_monitor_ui.ui_rects:
        if rect.collidepoint(mx, my):
            if name in CAMERA_NAMES:
                # 切换频道提示
                idx = CAMERA_NAMES.index(name)
                camera.switch_channel(idx)
            elif name == "旗舰":
                import random
                popup_text = random.choice(FLAGSHIP_HINTS)
                popup_timer = pygame.time.get_ticks()
            elif name == "桑多涅的房间":
                import random
                popup_text = random.choice(PLAYER_ROOM_HINTS)
                popup_timer = pygame.time.get_ticks()
            break

# ===================== 绘制函数 =====================
def draw_menu():
    if menu_bg is not None:
        screen.blit(menu_bg, (0, 0))

def draw_pause_menu():
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    overlay.set_alpha(160)
    overlay.fill(COLOR_BLACK)
    screen.blit(overlay, (0, 0))
    t_big = font_big.render("游戏已暂停", True, COLOR_WHITE)
    t1 = font.render("【空格】继续游戏", True, COLOR_WHITE)
    t2 = font.render("【M】返回主菜单", True, COLOR_RED)
    screen.blit(t_big, (SCREEN_WIDTH//2 - 160, 260))
    screen.blit(t1, (SCREEN_WIDTH//2 - 150, 330))
    screen.blit(t2, (SCREEN_WIDTH//2 - 150, 380))

def draw_gameover():
    screen.fill((40, 0, 0))
    t_fail = font.render("桑多涅被哥伦比娅抓住了！", True, COLOR_RED)
    t_back = font.render("【空格】返回主菜单", True, COLOR_WHITE)
    screen.blit(t_fail, (SCREEN_WIDTH//2 - 320, SCREEN_HEIGHT//2 - 40))
    screen.blit(t_back, (SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2))
    try:
        pygame.mixer.music.stop()
    except:
        pass

def draw_victory():
    screen.fill(COLOR_BLACK)
    t_win = font.render("天亮，今夜安全度过", True, COLOR_GREEN_SAFE)
    t1 = font.render("【空格】进入下一夜", True, COLOR_WHITE)
    t2 = font.render("【ESC】返回主菜单", True, COLOR_GRAY_LIGHT)
    screen.blit(t_win, (SCREEN_WIDTH//2 - 260, SCREEN_HEIGHT//2 - 60))
    screen.blit(t1, (SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2))
    screen.blit(t2, (SCREEN_WIDTH//2 - 200, SCREEN_HEIGHT//2 + 60)) 
    try:
        pygame.mixer.music.stop()
    except:
        pass

def draw_game(dt):
    global night_timer, current_scene, door_open, door_broken, is_repairing, repair_progress
    global jumpscare_active, jumpscare_start_time, jumpscare_fade_alpha

    # 更新跳脸
    update_jumpscare()

    # 底层房间背景
    if camera.open and not power.is_outage:
        # 绘制监控
        draw_monitor_fullscreen()
    else:
        # 玩家房间背景
        if door_open or door_broken:
            if player_room_open_bg is not None:
                screen.blit(player_room_open_bg, (0, 0))
            else:
                screen.fill((12, 12, 18))
        else:
            if player_room_closed_bg is not None:
                screen.blit(player_room_closed_bg, (0, 0))
            else:
                screen.fill((12, 12, 18))

        # 绘制房间内怪物
        if nant.path_val == PLAYER_ROOM_INDEX and (door_open or door_broken) and not nant.has_summoned:
            target_x = 919
            target_y = 541
            target_w = 1061 - 919
            target_h = 742 - 541
            if nant.monster_surf is not None:
                nant_big_surf = pygame.transform.smoothscale(nant.monster_surf, (target_w, target_h))
                screen.blit(nant_big_surf, (target_x, target_y))

        if columbia.path_val == PLAYER_ROOM_INDEX:
            col_x = (SCREEN_WIDTH - columbia.big_monster_w) // 2
            col_y = SCREEN_HEIGHT - columbia.big_monster_h - 20
            columbia.draw_in_player_room(screen, col_x, col_y)

        # 隐蔽罩
        if not columbia.is_catching:
            cover.draw(screen)

    # ========== 绘制跳脸贴图 ==========
    if jumpscare_active and jumpscare_img is not None:
        jumpscare_img.set_alpha(jumpscare_fade_alpha)
        screen.blit(jumpscare_img, (0, 0))

    # ========== 暂停时 ==========
    if not is_paused:
        cover.update_anim()
        power.update(camera.open, dt)
        night_timer += dt * 1000

        # 更新维修进度
        if is_repairing:
            repair_progress += dt * 1000
            if repair_progress >= DOOR_REPAIR_TIME:
                is_repairing = False
                door_broken = False
                repair_progress = 0

        # 五夜通关判定
        if night_timer >= NIGHT_DURATION_MS:
            write_all_log()
            if game_mode == 0 and current_night >= 5:
                current_scene = SCENE_MENU
            else:
                current_scene = SCENE_VICTORY
            try:
                pygame.mixer.music.stop()
            except:
                pass
            return

        # 更新哥伦比娅
        col_game_over, _, col_choice, col_trigger = columbia.update(cover.wearing, dt, current_night)
        if col_game_over:
            # 触发跳脸
            if not jumpscare_active:
                jumpscare_active = True
                jumpscare_start_time = pygame.time.get_ticks()
            return

        # 更新努昂诺塔
        nant_game_over, nant_choice, nant_trigger = nant.update(cover.wearing, door_open, columbia, current_night)
        if nant_game_over:
            write_all_log()
            current_scene = SCENE_GAMEOVER
            return

        # 检测门损坏触发
        if nant.trigger_door_break and not is_repairing:
            door_broken = True
            nant.trigger_door_break = False

        # 日志记录
        if show_debug and can_open_debug:
            if col_trigger:
                log_line = f"{{第{current_night}夜|{int(night_timer)}ms}}[哥伦比娅|{columbia.path_val}|{col_choice}]"
                game_log_buffer.append(log_line)
            if nant_trigger:
                log_line = f"{{第{current_night}夜|{int(night_timer)}ms}}[努昂诺塔|{nant.path_val}|{nant_choice}]"
                game_log_buffer.append(log_line)

    # ========== UI层 ==========
    if jumpscare_active:
        ui_color = (128, 0, 128)  
        unknown_text = True
    else:
        ui_color = COLOR_WHITE
        unknown_text = False

    # 电量条
    pygame.draw.rect(screen, COLOR_GRAY, (20, 20, 204, 26))
    if jumpscare_active:
        bar_color = (128, 0, 128)
        power_text_str = "???%"
    else:
        bar_color = power.get_bar_color()
        power_text_str = f"电量 {power.value:.1f}%"
    pygame.draw.rect(screen, bar_color, (22, 22, power.value * 2, 22))
    power_text = font.render(power_text_str, True, ui_color)
    screen.blit(power_text, (240, 20))

    # 时间
    clock_text = "未知" if unknown_text else time_to_clock(night_timer)
    night_text = font.render(f"第{current_night}夜 {clock_text}", True, ui_color)
    screen.blit(night_text, (20, 60))

    # 遮罩
    cover_text_str = "未知" if unknown_text else cover.get_status_text()
    cover_text = font.render(cover_text_str, True, ui_color if unknown_text else COLOR_BLUE_LIGHT)
    screen.blit(cover_text, (20, 100))

    # 门
    if unknown_text:
        door_text = font.render("未知", True, ui_color)
    else:
        if door_broken:
            if is_repairing:
                pct = repair_progress / DOOR_REPAIR_TIME * 100
                door_text = font.render(f"门：损坏  {pct:.0f}%", True, COLOR_RED)
            else:
                door_text = font.render("门：损坏 ", True, COLOR_RED)
        else:
            door_status = "开启" if door_open else "关闭"
            door_text = font.render(f"门：{door_status}", True, COLOR_YELLOW_WARN)
    screen.blit(door_text, (20, 140))

    # 操作提示
    if SHOW_CONTROL_HINT and not jumpscare_active:
        h1 = font.render("Q开关监控 W遮罩 E关门 R维修", True, COLOR_GRAY_LIGHT)
        h2 = font.render("F10隐藏提示 ESC暂停", True, COLOR_GRAY_LIGHT)
        screen.blit(h1, (20, 180))
        screen.blit(h2, (21, 210))

    # 调试面板
    if show_debug and can_open_debug:
        right_padding = 20
        debug_lines = [
            (f"监控:{camera.open} 频道:{CAMERA_NAMES[camera.current]}", COLOR_WHITE),
            (columbia.get_desc(), (255, 255, 0)),
            (nant.get_desc(), (255, 200, 100)),
            (f"电量:{power.value:.2f}", (255, 255, 0)),
            (f"计时:{int(night_timer)}ms", (255, 255, 0)),
        ]
        for idx, (text, color) in enumerate(debug_lines):
            text_surf = font.render(text, True, color)
            draw_x = SCREEN_WIDTH - right_padding - text_surf.get_width()
            screen.blit(text_surf, (draw_x, 20 + idx * 30))

    global popup_text, popup_timer
    if popup_text:
        now = pygame.time.get_ticks()
        if now - popup_timer > 2000:  
            popup_text = ""
        else:
            surf = font_popup.render(popup_text, True, (255, 255, 255))
            bg_surf = pygame.Surface((surf.get_width() + 60, surf.get_height() + 60))
            bg_surf.set_alpha(200)
            bg_surf.fill((0, 0, 0))
            bg_rect = bg_surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            screen.blit(bg_surf, bg_rect)
            text_rect = surf.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            screen.blit(surf, text_rect)

    update_current_hum()

# ===================== 主循环 =====================
running = True
while running:
    dt = clock.tick(FPS) / 1000
    event_list = pygame.event.get()

    for ev in event_list:
        if ev.type == pygame.QUIT:
            write_all_log()
            pygame.mixer.music.stop()
            running = False

        if ev.type == pygame.KEYDOWN:
            # 调试开关
            if ev.key == pygame.K_p and can_open_debug:
                show_debug = not show_debug
                print("调试开关：", show_debug)

            # 全屏切换
            if ev.key == pygame.K_F11:
                flags = screen.get_flags()
                if flags & pygame.NOFRAME:
                    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                else:
                    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)

            # ESC
            if ev.key == pygame.K_ESCAPE:
                if current_scene == SCENE_GAME:
                    current_scene = SCENE_PAUSE
                    is_paused = True
                elif current_scene == SCENE_PAUSE:
                    current_scene = SCENE_GAME
                    is_paused = False
                elif current_scene == SCENE_VICTORY:
                    write_all_log()
                    current_scene = SCENE_MENU

            # 主菜单按键
            if current_scene == SCENE_MENU:
                if ev.key == pygame.K_1:
                    game_mode = 0
                    current_night = 1
                    init_game_scene()
                    current_scene = SCENE_GAME
                if ev.key == pygame.K_2:
                    game_mode = 1
                    current_night = 1
                    init_game_scene()
                    current_scene = SCENE_GAME
                if ev.key == pygame.K_3:
                    write_all_log()
                    running = False

            # 暂停界面
            if current_scene == SCENE_PAUSE:
                if ev.key == pygame.K_SPACE:
                    current_scene = SCENE_GAME
                    is_paused = False
                if ev.key == pygame.K_m:
                    write_all_log()
                    pygame.mixer.music.stop()
                    current_scene = SCENE_MENU

            # 胜利界面
            if current_scene == SCENE_VICTORY:
                if ev.key == pygame.K_SPACE:
                    current_night += 1
                    init_game_scene()
                    current_scene = SCENE_GAME

            # 游戏内操作
            if current_scene == SCENE_GAME:
                if ev.key == pygame.K_F10:
                    SHOW_CONTROL_HINT = not SHOW_CONTROL_HINT
                if ev.key == pygame.K_o or ev.key == pygame.K_0 or ev.key == pygame.K_q:
                    camera.toggle()
                if ev.key == pygame.K_w:
                    cover.toggle()
                if ev.key == pygame.K_e:
                    if not cover.wearing and not door_broken:
                        door_open = not door_open
                if ev.key == pygame.K_r:
                    if door_broken and not is_repairing:
                        is_repairing = True
                        repair_progress = 0

            # 失败界面
            if current_scene == SCENE_GAMEOVER:
                if ev.key == pygame.K_SPACE:
                    current_scene = SCENE_MENU

        # 鼠标点击事件
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and current_scene == SCENE_GAME:
            mx, my = ev.pos
            if camera.open and not power.is_outage:
                handle_monitor_click(mx, my)

    # 场景渲染
    if current_scene == SCENE_MENU:
        draw_menu()
    elif current_scene == SCENE_GAME:
        draw_game(dt)
    elif current_scene == SCENE_PAUSE:
        draw_game(dt)
        draw_pause_menu()
    elif current_scene == SCENE_GAMEOVER:
        draw_gameover()
    elif current_scene == SCENE_VICTORY:
        draw_victory()

    pygame.display.flip()

pygame.quit()
sys.exit()
