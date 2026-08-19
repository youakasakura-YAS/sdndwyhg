# Copyright (c) 2026 youakasakura‑YAS
# SPDX‑License‑Identifier: MIT
# Note: System architecture and module design conceived by human.
# Code assisted by AI, manually modified, debugged and integrated by human.
import pygame
from config import SCREEN_HEIGHT, SCREEN_WIDTH, COVER_IMG_PATH, COVER_MAX_TIME_MS
class CoverSystem:
    def __init__(self):
        self.wearing = False
        # 加载遮罩贴图
        try:
            self.img = pygame.image.load(COVER_IMG_PATH).convert_alpha()
            self.img = pygame.transform.scale(self.img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except Exception:
            self.img = None
        # 滑动动画参数
        self.anim_y = -SCREEN_HEIGHT
        self.anim_speed = 24
        self.is_animating = False
        # 限时
        self.start_wear_tick = 0
        self.MAX_WEAR_MS = COVER_MAX_TIME_MS
        # CD
        self.cooldown_end_tick = 0
        self.COOLDOWN_MS = 5000
    def toggle(self):
        now = pygame.time.get_ticks()
        if now < self.cooldown_end_tick:
            return
        self.wearing = not self.wearing
        self.is_animating = True
        if self.wearing:
            self.start_wear_tick = now
        else:
            self.cooldown_end_tick = now + self.COOLDOWN_MS
    def update_anim(self):
        now = pygame.time.get_ticks()
        # 满时长
        if self.wearing and not self.is_animating:
            if now - self.start_wear_tick >= self.MAX_WEAR_MS:
                self.wearing = False
                self.is_animating = True
                self.cooldown_end_tick = now + self.COOLDOWN_MS
        # 滑动动画
        if not self.is_animating:
            return
        if self.wearing:
            # 带上
            self.anim_y += self.anim_speed
            if self.anim_y >= 0:
                self.anim_y = 0
                self.is_animating = False
        else:
            # 摘下
            self.anim_y -= self.anim_speed
            if self.anim_y <= -SCREEN_HEIGHT:
                self.anim_y = -SCREEN_HEIGHT
                self.is_animating = False
    def draw(self, screen):
        if self.img is None:
            return
        screen.blit(self.img, (0, self.anim_y))
    def get_status_text(self):
        now = pygame.time.get_ticks()
        # 冷却提示
        if now < self.cooldown_end_tick:
            cd_left = (self.cooldown_end_tick - now) / 1000
            return f"隐蔽罩冷却中，剩余 {cd_left:.1f}s"
        if not self.wearing:
            return "隐蔽罩：未佩戴"
        # 剩余时长
        wear_left = (self.MAX_WEAR_MS - (now - self.start_wear_tick)) / 1000
        wear_left = max(0, wear_left)
        return f"隐蔽罩佩戴中，剩余 {wear_left:.1f}s / 23.0s"