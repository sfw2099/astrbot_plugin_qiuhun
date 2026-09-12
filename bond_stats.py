# -*- coding: utf-8 -*-
"""求婚跨天统计（bond_stats.json）。

追踪：
- marry_streak：连续结为夫妻天数（三生三世）
- propose_no_reply：连续求婚无回应次数（知我相思苦）
- cut_count / sever_count：被斩/主动斩羁绊线累计（升级制成就）
- matchmaker_count / swap_count：点鸳鸯/换连理累计成功
- last_marry_date / last_active_date：连续天数判定用
"""

import json
import os
import threading
from datetime import datetime, timedelta

DEFAULTS = {
    "marry_streak": 0,
    "last_marry_date": "",
    "propose_no_reply": 0,
    "cut_count": 0,
    "sever_count": 0,
    "matchmaker_count": 0,
    "swap_count": 0,
}


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _yesterday() -> str:
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")


class BondStats:
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

    def _uid(self, uid: str) -> dict:
        d = self._data.setdefault(str(uid), {})
        for k, v in DEFAULTS.items():
            d.setdefault(k, v)
        return d

    # ---------- 三生三世 ----------

    def record_marry(self, uid: str):
        """记录今天结为夫妻。返回更新后的连续天数。"""
        with self._lock:
            d = self._uid(uid)
            today = _today()
            if d["last_marry_date"] == today:
                return d["marry_streak"]
            if d["last_marry_date"] == _yesterday():
                d["marry_streak"] += 1
            else:
                d["marry_streak"] = 1
            d["last_marry_date"] = today
            self._save()
            return d["marry_streak"]

    def get_marry_streak(self, uid: str) -> int:
        d = self._uid(uid)
        # 隔天未续则清零展示
        if d["last_marry_date"] not in (_today(), _yesterday()):
            return 0
        return d["marry_streak"]

    # ---------- 求婚无回应 ----------

    def record_no_reply(self, uid: str) -> int:
        with self._lock:
            d = self._uid(uid)
            d["propose_no_reply"] += 1
            self._save()
            return d["propose_no_reply"]

    def reset_no_reply(self, uid: str):
        with self._lock:
            d = self._uid(uid)
            if d["propose_no_reply"]:
                d["propose_no_reply"] = 0
                self._save()

    # ---------- 累计计数 ----------

    def add_cut(self, uid: str, n: int = 1) -> int:
        """被斩 +n。返回最新累计。"""
        with self._lock:
            d = self._uid(uid)
            d["cut_count"] += int(n)
            self._save()
            return d["cut_count"]

    def add_sever(self, uid: str, n: int = 1) -> int:
        with self._lock:
            d = self._uid(uid)
            d["sever_count"] += int(n)
            self._save()
            return d["sever_count"]

    def add_matchmaker(self, uid: str) -> int:
        with self._lock:
            d = self._uid(uid)
            d["matchmaker_count"] += 1
            self._save()
            return d["matchmaker_count"]

    def add_swap(self, uid: str) -> int:
        with self._lock:
            d = self._uid(uid)
            d["swap_count"] += 1
            self._save()
            return d["swap_count"]

    def get(self, uid: str, key: str) -> int:
        return int(self._uid(str(uid)).get(key, 0))
