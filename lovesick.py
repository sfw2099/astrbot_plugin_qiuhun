# -*- coding: utf-8 -*-
"""相思树下档案（lovesick.json）：被【相思树下】道具清除的羁绊线按天保存。"""

import json
import os
import threading
from datetime import datetime


class LovesickStore:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._lock = threading.RLock()
        self._data = {}
        self._load()

    def _load(self):
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        except Exception:
            self._data = {}

    def _save(self):
        tmp = self.file_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.file_path)

    def save_bonds(self, uid: str, bonds: list):
        """保存被清除的羁绊线。bonds: [{user_id, wife_id, wife_name, ...}]。"""
        with self._lock:
            date = datetime.now().strftime("%Y-%m-%d")
            u = self._data.setdefault(str(uid), {})
            day = u.setdefault(date, [])
            day.extend(bonds)
            self._save()

    def get_bonds(self, uid: str, date: str = None) -> list:
        u = self._data.get(str(uid), {})
        if date is None:
            # 全部日期合并
            out = []
            for d in sorted(u.keys()):
                out.extend(u[d])
            return out
        return list(u.get(date, []))

    def count(self, uid: str) -> int:
        return len(self.get_bonds(uid))
