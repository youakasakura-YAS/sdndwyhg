# Copyright (c) 2026 youakasakura‑YAS
# SPDX‑License‑Identifier: MIT
# Note: System architecture and module design conceived by human.
# Code assisted by AI, manually modified, debugged and integrated by human.
from config import COLOR_GREEN_SAFE, COLOR_YELLOW_WARN, COLOR_RED
class PowerSystem:
    def __init__(self):
        self.value = 100.0
        self.drain_idle = 0.011 
        self.drain_cam = 0.109
        self.is_outage = False
    def update(self, cam_open: bool, dt: float):
        drain = self.drain_cam if cam_open else self.drain_idle
        self.value -= drain * dt
        if self.value <= 0:
            self.value = 0
            self.is_outage = True
    def get_bar_color(self):
        if self.value > 40:
            return COLOR_GREEN_SAFE
        elif self.value > 15:
            return COLOR_YELLOW_WARN
        return COLOR_RED