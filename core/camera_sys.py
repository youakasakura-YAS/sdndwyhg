# Copyright (c) 2026 youakasakura‑YAS
# SPDX‑License‑Identifier: MIT
# Note: System architecture and module design conceived by human.
# Code assisted by AI, manually modified, debugged and integrated by human.
from config import CAMERA_COUNT
class CameraSystem:
    def __init__(self):
        self.open = False
        self.current = 0
    def toggle(self):
        self.open = not self.open
    def switch_channel(self, idx: int):
        if 0 <= idx < CAMERA_COUNT:
            self.current = idx