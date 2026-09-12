# -*- coding: utf-8 -*-
"""求婚插件 → 秋烨枢纽的连接层。

- get_hub(context)：从 star 注册表取秋烨实例（懒加载，每次调用时取，规避加载顺序问题）。
- bond 读写：优先秋烨 API；秋烨不可用时降级到本插件本地 fallback 文件（手动迁移期间兜底）。
- 活跃池：直接读秋烨 active_users.json（文件约定读，避免实例依赖）。
"""

import json
import os
import time

HUB_NAME = "astrbot_plugin_qiuye"


def get_hub(context):
    try:
        meta = context.get_registered_star(HUB_NAME)
        inst = getattr(meta, "star_cls", None)
        if inst is not None and getattr(inst, "hub_ready", False):
            return inst
    except Exception:
        pass
    return None


class BondLink:
    """羁绊读写：秋烨优先，本地 fallback 兜底。"""

    def __init__(self, fallback_file: str):
        self.fallback_file = fallback_file
        self._lock = __import__("threading").Lock()

    def _load(self) -> dict:
        try:
            with open(self.fallback_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self, data: dict):
        os.makedirs(os.path.dirname(self.fallback_file), exist_ok=True)
        with open(self.fallback_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _clamp(v: int) -> int:
        return max(0, min(99, int(v)))

    def get_bond(self, context, uid: str, name: str = "") -> int:
        hub = get_hub(context)
        if hub is not None:
            try:
                return int(hub.get_bond(uid, name))
            except Exception:
                pass
        return int(self._load().get(str(uid), {}).get("bond", 50))

    def add_bond(self, context, uid: str, delta: int, name: str = "") -> int:
        hub = get_hub(context)
        if hub is not None:
            try:
                return int(hub.add_bond(uid, delta, name))
            except Exception:
                pass
        with self._lock:
            data = self._load()
            u = data.setdefault(str(uid), {})
            u["bond"] = self._clamp(u.get("bond", 50) + int(delta))
            if name:
                u["name"] = name
            self._save(data)
            return u["bond"]

    def set_bond(self, context, uid: str, value: int, name: str = "") -> int:
        hub = get_hub(context)
        if hub is not None:
            try:
                cur = int(hub.get_bond(uid, name))
                return int(hub.add_bond(uid, self._clamp(value) - cur, name))
            except Exception:
                pass
        with self._lock:
            data = self._load()
            u = data.setdefault(str(uid), {})
            u["bond"] = self._clamp(value)
            if name:
                u["name"] = name
            self._save(data)
            return u["bond"]


class ActivePoolLink:
    """活跃池：优先秋烨实例 API；否则直接读秋烨 active_users.json。"""

    def __init__(self, qiuye_data_dir: str):
        # 约定路径：data/astrbot_plugin_qiuye/active_users.json
        self.active_file = os.path.join(qiuye_data_dir, "active_users.json")

    def get_pool(self, context, group_id: str) -> dict:
        hub = get_hub(context)
        if hub is not None:
            try:
                return dict(hub.get_active_pool(group_id))
            except Exception:
                pass
        try:
            with open(self.active_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return dict(data.get(str(group_id), {}))
        except Exception:
            return {}

    def remove_uids(self, context, group_id: str, uids):
        hub = get_hub(context)
        if hub is not None:
            try:
                hub.store.remove_active(group_id, uids)
            except Exception:
                pass

    def cleanup(self, context, group_id: str):
        hub = get_hub(context)
        if hub is not None:
            try:
                hub.store.cleanup_inactive(group_id)
            except Exception:
                pass


def record_plugin_use(context, uid: str, name: str = ""):
    """向秋烨记录「用户使用了求婚插件」（尽力而为）。"""
    hub = get_hub(context)
    if hub is not None:
        try:
            hub.record_plugin_use(uid, "astrbot_plugin_qiuhun", name)
        except Exception:
            pass


def touch_user(context, uid: str, name: str = ""):
    hub = get_hub(context)
    if hub is not None:
        try:
            hub.store.touch(uid, name)
        except Exception:
            pass


def now_ts() -> float:
    return time.time()
