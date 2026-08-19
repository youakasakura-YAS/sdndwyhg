# Copyright (c) 2026 youakasakura‑YAS
# SPDX‑License‑Identifier: MIT
# Note: System architecture and module design conceived by human.
# Code assisted by AI, manually modified, debugged and integrated by human.
import random
import pygame
from config import *

class Columbia:
    def __init__(self):
        self.path_val = 0  
        self.state = STATE_WANDER
        self.last_move_tick = pygame.time.get_ticks()
        self.move_cd_ms = random.randint(COLUMBIA_BASE_CD_MIN, COLUMBIA_BASE_CD_MAX)
        self.room_arrive_tick = 0
        self.room_stay_sec = random.randint(5, 15)
        self.backstep_remain = 0
        self.room_enter_count = 0
        self.in_room_wait = False
        self.play_leave_sound = False
        self.is_catching = False
        self.last_choice = "无"
        self.leave_room_tick = -10000  
        self.channel = pygame.mixer.Channel(1)  # 使用通道1

        # 跳脸状态
        self.jumpscare_active = False
        self.jumpscare_start_time = 0

        # 怪物贴图尺寸
        self.monster_w = int(140 * MONSTER_SCALE_MONITOR)
        self.monster_h = int(180 * MONSTER_SCALE_MONITOR)
        self.big_monster_w = int(300 * MONSTER_SCALE_ROOM)
        self.big_monster_h = int(380 * MONSTER_SCALE_ROOM)

        try:
            raw_img = pygame.image.load(MONSTER_IMG_PATH).convert_alpha()
            self.monster_surf = pygame.transform.smoothscale(raw_img, (self.monster_w, self.monster_h))
        except Exception as e:
            print("哥伦比娅贴图加载失败:", e)
            self.monster_surf = None

        # 音效加载
        self.sound_clk = None
        self.sound_clk3 = None
        self.sound_jrfj = None
        self.sound_bzd = None
        try:
            self.sound_clk = pygame.mixer.Sound(CLK_SOUND_PATH)
            self.sound_clk.set_volume(0.6)
            self.sound_clk3 = pygame.mixer.Sound(CLK3_SOUND_PATH)
            self.sound_clk3.set_volume(0.6)
            self.sound_jrfj = pygame.mixer.Sound(JRFJ_SOUND_PATH)
            self.sound_jrfj.set_volume(0.6)
            self.sound_bzd = pygame.mixer.Sound(BZD_SOUND_PATH)
            self.sound_bzd.set_volume(0.6)
        except Exception as e:
            print("哥伦比娅音效加载失败:", e)

        # 计算距离
        self.dist_to_player = {}
        self._build_dist_cache()

    def _build_dist_cache(self):
        target = PATH_NAMES[PLAYER_ROOM_INDEX]
        for name in PATH_NAMES:
            dist = {name: 0}
            queue = [name]
            while queue:
                cur = queue.pop(0)
                if cur == target:
                    break
                for nxt in PATH_GRAPH.get(cur, []):
                    if nxt not in dist:
                        dist[nxt] = dist[cur] + 1
                        queue.append(nxt)
            self.dist_to_player[name] = dist.get(target, 999)

    def reset(self, night_num=1):
        self.path_val = 0
        self.state = STATE_WANDER
        self.last_move_tick = pygame.time.get_ticks()
        decay = 0.9 ** (night_num - 1)
        cd_min = max(COLUMBIA_MIN_CD, int(COLUMBIA_BASE_CD_MIN * decay))
        cd_max = max(COLUMBIA_MIN_CD, int(COLUMBIA_BASE_CD_MAX * decay))
        self.move_cd_ms = random.randint(cd_min, cd_max)
        self.room_arrive_tick = 0
        self.room_stay_sec = random.randint(5, 15)
        self.backstep_remain = 0
        self.room_enter_count = 0
        self.in_room_wait = False
        self.play_leave_sound = False
        self.is_catching = False
        self.last_choice = "无"
        self.leave_room_tick = -10000
        self.jumpscare_active = False
        self.jumpscare_start_time = 0

    def _get_double_step_chance(self, night_num):
        if night_num < COLUMBIA_DOUBLE_STEP_START_NIGHT:
            return 0.0
        chance = COLUMBIA_DOUBLE_STEP_BASE + (night_num - COLUMBIA_DOUBLE_STEP_START_NIGHT) * COLUMBIA_DOUBLE_STEP_INCREMENT
        return min(chance, COLUMBIA_DOUBLE_STEP_MAX)

    def random_step(self, night_num: int) -> str:
        current_name = PATH_NAMES[self.path_val]
        neighbors = PATH_GRAPH.get(current_name, [])
        if not neighbors:
            return "停留"

        if self.backstep_remain > 0:
            p_back = 0.7
            self.backstep_remain -= 1
        else:
            p_back = 0.3

        # 决定后退还是前进
        if random.random() < p_back:
            far = [n for n in neighbors if self.dist_to_player[n] > self.dist_to_player[current_name]]
            if far:
                chosen = random.choice(far)
                self.path_val = PATH_INDEX[chosen]
                return "后退"
            else:
                return "停留"
        else:           
            steps = 2 if random.random() < self._get_double_step_chance(night_num) else 1
            new_name = current_name
            for _ in range(steps):
                nearer = [n for n in neighbors if self.dist_to_player[n] < self.dist_to_player[new_name]]
                if nearer:
                    new_name = random.choice(nearer)
                else:
                    if neighbors:
                        new_name = random.choice(neighbors)
                    break
            if new_name != current_name:
                self.path_val = PATH_INDEX[new_name]
                return f"前进{steps}步" if steps > 1 else "前进1步"
            else:
                return "停留"

    def update(self, cover_wearing: bool, dt, night_num: int) -> tuple[bool, int, str, bool]:
        if self.jumpscare_active:
            return True, self.path_val, "未知", True
        now = pygame.time.get_ticks()
        old_path = self.path_val
        trigger_choice = False
        choice_result = "停留"

        if self.jumpscare_active:
            return False, old_path, "未知", False


        # 记录离开房间时间
        if old_path == PLAYER_ROOM_INDEX and self.state != STATE_IN_ROOM:
            self.leave_room_tick = now

        # 抉择冷却
        if now - self.last_move_tick >= self.move_cd_ms:
            trigger_choice = True
            r_act = random.random()
            if r_act < 0.7:
                choice_result = self.random_step(night_num)
            self.last_move_tick = now
            decay = 0.9 ** (night_num - 1)
            cd_min = max(COLUMBIA_MIN_CD, int(COLUMBIA_BASE_CD_MIN * decay))
            cd_max = max(COLUMBIA_MIN_CD, int(COLUMBIA_BASE_CD_MAX * decay))
            self.move_cd_ms = random.randint(cd_min, cd_max)
            self.last_choice = choice_result

        # 抵达玩家房间
        if self.path_val == PLAYER_ROOM_INDEX and self.state != STATE_IN_ROOM:
            self.state = STATE_IN_ROOM
            self.room_arrive_tick = now
            self.room_stay_sec = random.randint(5, 15)
            self.room_enter_count += 1
            self.in_room_wait = True
            self.play_leave_sound = False
            if self.sound_jrfj:
                self.sound_jrfj.stop()
                self.sound_jrfj.play()

        # 房间停留结束
        if self.state == STATE_IN_ROOM and self.in_room_wait:
            stay_ms = now - self.room_arrive_tick
            if stay_ms >= self.room_stay_sec * 1000 and not self.play_leave_sound:
                self.play_leave_sound = True
                if self.room_enter_count >= 4:
                    if self.sound_clk3:
                        self.sound_clk3.stop()
                        self.sound_clk3.play()
                else:
                    if self.sound_clk:
                        self.sound_clk.stop()
                        self.sound_clk.play()

            if self.play_leave_sound and not pygame.mixer.get_busy():
                self.path_val -= 1
                self.backstep_remain = 3
                self.state = STATE_WANDER
                self.in_room_wait = False
                self.play_leave_sound = False
                self.room_arrive_tick = 0
                self.leave_room_tick = now

         # 死亡判定
            if self.state == STATE_IN_ROOM:
                stay_ms = now - self.room_arrive_tick
                grace_over = stay_ms >= ROOM_GRACE_TIME
                if not cover_wearing and grace_over and not self.is_catching:
                    self.is_catching = True
                    # 播放抓捕音效
                    if self.sound_bzd:
                        self.channel.stop()
                        self.channel.play(self.sound_bzd)
                    return True, self.path_val, "抓捕触发", True

        return False, self.path_val, choice_result, trigger_choice

    def draw_in_monitor(self, surface, draw_x, draw_y):
        if self.monster_surf is None:
            return
        surface.blit(self.monster_surf, (draw_x, draw_y))

    def draw_in_player_room(self, surface, draw_x, draw_y):
        if self.monster_surf is None:
            return
        big_img = pygame.transform.smoothscale(self.monster_surf, (self.big_monster_w, self.big_monster_h))
        surface.blit(big_img, (draw_x, draw_y))

    def get_desc(self):
        if self.is_catching:
            return "哥伦比娅：袭击中"
        pos_name = LOC_NAME_MAP.get(self.path_val, "未知区域")
        return f"哥伦比娅：{pos_name} | {self.last_choice}"

    def enter_catch_room(self, trigger_tick: int):
        self.path_val = PLAYER_ROOM_INDEX
        self.state = STATE_IN_ROOM
        self.room_arrive_tick = trigger_tick
        self.is_catching = True
        if self.sound_bzd:
            self.channel.stop()
            self.channel.play(self.sound_bzd)
        self.jumpscare_active = True