# Copyright (c) 2026 youakasakura‑YAS
# SPDX‑License‑Identifier: MIT
# Note: System architecture and module design conceived by human.
# Code assisted by AI, manually modified, debugged and integrated by human.
import random
import pygame
from config import *
from core.columbia import Columbia

class Nuantanota:
    def __init__(self):
        r = random.random()
        self.path_val = 0 if r < 0.6 else 2
        self.state = STATE_WANDER
        self.last_decision_tick = pygame.time.get_ticks()
        self.decision_cd_ms = random.randint(NANT_BASE_CD_MIN, NANT_BASE_CD_MAX)
        self.backstep_remain = 0
        self.room_enter_tick = 0
        self.in_room_wait = False
        self.frozen = False
        self.last_choice = "无"
        self.has_summoned = False
        self.trigger_door_break = False
        self.monster_w = int(130 * MONSTER_SCALE_MONITOR)
        self.monster_h = int(170 * MONSTER_SCALE_MONITOR)
        self.big_monster_w = int(280 * MONSTER_SCALE_ROOM)
        self.big_monster_h = int(360 * MONSTER_SCALE_ROOM)

        try:
            raw_img = pygame.image.load(NANT_IMG_PATH).convert_alpha()
            self.monster_surf = pygame.transform.smoothscale(raw_img, (self.monster_w, self.monster_h))
        except Exception as e:
            print("努昂诺塔贴图加载失败:", e)
            self.monster_surf = None

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

    def reset(self, night_num: int):
        r = random.random()
        self.path_val = 0 if r < 0.6 else 2
        self.state = STATE_WANDER
        self.last_decision_tick = pygame.time.get_ticks()
        self.backstep_remain = 0
        self.room_enter_tick = 0
        self.in_room_wait = False
        self.frozen = False
        self.last_choice = "无"
        self.has_summoned = False
        self.trigger_door_break = False

        decay = 0.9 ** (night_num - 1)
        cd_min = max(NANT_MIN_CD, int(NANT_BASE_CD_MIN * decay))
        cd_max = max(NANT_MIN_CD, int(NANT_BASE_CD_MAX * decay))
        self.decision_cd_ms = random.randint(cd_min, cd_max)

    def _get_double_step_chance(self, night_num: int) -> float:
        chance = NANT_BASE_DOUBLE_STEP + (night_num - 1) * 0.05
        return min(chance, NANT_MAX_DOUBLE_STEP)

    def _count_channel_monsters(self, channel: int, columbia: Columbia) -> int:
        count = 0
        if columbia.path_val == channel:
            count += 1
        if self.path_val == channel:
            count += 1
        return count

    def _can_enter_room(self, columbia: Columbia) -> bool:
        now = pygame.time.get_ticks()
        if columbia.path_val == PLAYER_ROOM_INDEX or columbia.is_catching:
            return False
        if now - columbia.leave_room_tick < 3000:
            return False
        return True

    def update(self, cover_wearing: bool, door_open: bool, columbia: Columbia, night_num: int) -> tuple[bool, str, bool]:
        now = pygame.time.get_ticks()
        trigger_choice = False
        choice_result = "停留"

        if self.has_summoned:
            return False, "已召唤", False

        if self.path_val == 5 and not self._can_enter_room(columbia):
            self.frozen = True
            return False, "冻结中", False
        elif self.frozen:
            self.frozen = False
            self.path_val = PLAYER_ROOM_INDEX
            self.state = STATE_IN_ROOM
            self.room_enter_tick = now
            self.in_room_wait = True
            self.last_choice = "进入房间"
            return False, "进入房间", True

        # ========== 房间内逻辑 ==========
        if self.state == STATE_IN_ROOM and self.in_room_wait:
            stay_ms = now - self.room_enter_tick

            # 哥伦比娅已在房间
            if columbia.path_val == PLAYER_ROOM_INDEX or columbia.is_catching:
                self.path_val = 5  
                self.state = STATE_WANDER
                self.in_room_wait = False
                self.backstep_remain = 2
                self.trigger_door_break = True
                return False, "后退离开", True

            if stay_ms >= NANT_ROOM_GRACE and door_open:
                columbia.enter_catch_room(now)
                return False, "召唤哥伦比娅", True

            if now - self.last_decision_tick >= self.decision_cd_ms:
                trigger_choice = True
                r = random.random()
                if r < NANT_BACKWARD_IN_ROOM:
                    self.path_val = 5
                    self.state = STATE_WANDER
                    self.in_room_wait = False
                    self.backstep_remain = 2
                    self.trigger_door_break = True
                    choice_result = "后退离开"
                else:
                    choice_result = "停留"
                self.last_decision_tick = now
                self.last_choice = choice_result

                decay = 0.9 ** (night_num - 1)
                cd_min = max(NANT_MIN_CD, int(NANT_BASE_CD_MIN * decay))
                cd_max = max(NANT_MIN_CD, int(NANT_BASE_CD_MAX * decay))
                self.decision_cd_ms = random.randint(cd_min, cd_max)

            return False, choice_result, trigger_choice

        if now - self.last_decision_tick >= self.decision_cd_ms:
            trigger_choice = True
            r_act = random.random()

            if r_act < 0.7:
                current_name = PATH_NAMES[self.path_val]
                neighbors = PATH_GRAPH.get(current_name, [])
                if not neighbors:
                    choice_result = "停留"
                else:
                    # 后退或前进
                    if self.backstep_remain > 0:
                        p_back = 0.8
                        self.backstep_remain -= 1
                    else:
                        p_back = 0.2

                    if random.random() < p_back:
                        # 后退
                        far = [n for n in neighbors if self.dist_to_player[n] > self.dist_to_player[current_name]]
                        if far:
                            chosen = random.choice(far)
                            self.path_val = PATH_INDEX[chosen]
                            choice_result = "后退"
                        else:
                            choice_result = "停留"
                    else:
                        # 前进
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
                        target = PATH_INDEX[new_name]
                        # 检查频道容量
                        if self._count_channel_monsters(target, columbia) >= MONSTER_MAX_IN_CHANNEL:
                            choice_result = "行动取消"
                        elif target == PLAYER_ROOM_INDEX and not self._can_enter_room(columbia):
                            self.frozen = True
                            choice_result = "冻结(等待进入)"
                        else:
                            self.path_val = target
                            if self.path_val == PLAYER_ROOM_INDEX:
                                self.state = STATE_IN_ROOM
                                self.room_enter_tick = now
                                self.in_room_wait = True
                                choice_result = "进入房间"
                            else:
                                choice_result = f"前进{steps}步" if steps > 1 else "前进1步"
            else:
                choice_result = "停留"

            self.last_decision_tick = now
            self.last_choice = choice_result

            decay = 0.9 ** (night_num - 1)
            cd_min = max(NANT_MIN_CD, int(NANT_BASE_CD_MIN * decay))
            cd_max = max(NANT_MIN_CD, int(NANT_BASE_CD_MAX * decay))
            self.decision_cd_ms = random.randint(cd_min, cd_max)

        return False, self.last_choice, trigger_choice

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
        status = "冻结中" if self.frozen else self.last_choice
        pos_name = LOC_NAME_MAP.get(self.path_val, "未知区域")
        return f"努昂诺塔：{pos_name} | {status}"