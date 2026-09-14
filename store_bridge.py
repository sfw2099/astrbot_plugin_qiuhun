# -*- coding: utf-8 -*-
"""求婚插件的道具/成就桥接层（走秋烨统一背包）。

接口与猜诗句插件的 StoreBridge 同名同语义，数据全部经秋烨枢纽。
诗句积累接口保留但为空实现（求婚插件不使用）。
"""

import time

from . import hub_link


class StoreBridge:
    """兼容 self.pm 调用面。"""

    def __init__(self, context):
        self.context = context

    def _hub(self):
        return hub_link.get_hub(self.context)

    def _name_of(self, uid, name=""):
        if name:
            return name
        hub = self._hub()
        if hub is not None:
            try:
                return hub.get_user(str(uid)).get("name") or f"用户{uid}"
            except Exception:
                pass
        return f"用户{uid}"

    def _uid_name(self, uid):
        return self._name_of(uid)

    # ---------- 诗句积累（求婚插件不使用，接口兼容） ----------

    def record_verse(self, uid, text, name=""):
        return 0

    def get_verses(self, uid):
        return {}

    def inc_stat(self, uid, key, amount=1, name=""):
        pass

    # ---------- 成就（秋烨） ----------

    def unlock_achievement(self, uid, ach_id, name=""):
        hub = self._hub()
        if hub is None:
            return False
        try:
            return bool(hub.unlock_achievement(uid, ach_id, plugin="astrbot_plugin_qiuhun", name=name))
        except Exception:
            return False

    def get_achievements(self, uid):
        hub = self._hub()
        if hub is None:
            return {}
        try:
            return dict(hub.get_achievements(uid))
        except Exception:
            return {}

    def check_verse_achievements(self, uid, name=""):
        return []

    # ---------- 道具（秋烨） ----------

    def add_item(self, uid, item, n=1, name=""):
        hub = self._hub()
        if hub is None:
            return 0
        try:
            return int(hub.add_item(uid, item, n, name))
        except Exception:
            return 0

    def get_items(self, uid, name=""):
        hub = self._hub()
        if hub is None:
            return {}
        try:
            return dict(hub.get_items(uid, name))
        except Exception:
            return {}

    def item_count(self, uid, item, name=""):
        hub = self._hub()
        if hub is None:
            return 0
        try:
            return int(hub.item_count(uid, item, name))
        except Exception:
            return 0

    def consume_item(self, uid, item, n=1, name=""):
        hub = self._hub()
        if hub is None:
            return False
        try:
            return bool(hub.consume_item(uid, item, n, name))
        except Exception:
            return False

    def take_random_item(self, from_uid, to_uid, name_from="", name_to=""):
        import random as _r
        inv = self.get_items(from_uid, name_from)
        owned = [k for k, v in inv.items() if v and int(v) > 0]
        if not owned:
            return None
        item = _r.choice(owned)
        self.consume_item(from_uid, item, 1, name_from)
        self.add_item(to_uid, item, 1, name_to)
        return item

    # ---------- 抽道具保底（秋烨） ----------

    def get_draw_bonus(self, uid, name=""):
        hub = self._hub()
        if hub is None:
            return 0
        try:
            return int(hub.get_draw_bonus(uid, name))
        except Exception:
            return 0

    def reset_draw_bonus(self, uid, name=""):
        hub = self._hub()
        if hub is None:
            return
        try:
            hub.reset_draw_bonus(uid, name)
        except Exception:
            pass

    def add_draw_bonus(self, uid, step, name=""):
        hub = self._hub()
        if hub is None:
            return
        try:
            hub.add_draw_bonus(uid, step, name)
        except Exception:
            pass
