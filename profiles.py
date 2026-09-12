# -*- coding: utf-8 -*-
"""求婚域个人档案（profiles/{uid}.json）。

原 autumn_blaze 的 ProfileManager 精简版：
- 运势(fortune)与羁绊(bond)已移至秋烨枢纽档案，本文件不再存储；
- COC 骰子判定所需的 bond 通过 hub_link 从秋烨读取；
- 保留求婚域自身字段（抽老婆计数/求婚状态/married_to 等）。
"""

import json
import os
import random
from datetime import datetime

DEFAULT_PROFILE = {
    "married_to": None,
    "yesterday_proposed_to": None,
    "proposed_today": False,
    "proposed_to_today": None,
    "drew_wife_today": False,
    "wife_draw_count_today": 0,
    "draw_date": "",
    "last_propose_date": "",
}


def _today_str():
    return datetime.now().strftime("%Y%m%d")


class ProfileManager:
    def __init__(self, profiles_dir: str):
        self.profiles_dir = profiles_dir
        os.makedirs(profiles_dir, exist_ok=True)

    def _file_path(self, user_id: str) -> str:
        return os.path.join(self.profiles_dir, f"{user_id}.json")

    def get_profile(self, user_id: str) -> dict:
        path = self._file_path(user_id)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    profile = json.load(f)
                for k, v in DEFAULT_PROFILE.items():
                    if k not in profile:
                        profile[k] = v
                return profile
            except Exception:
                pass
        profile = dict(DEFAULT_PROFILE)
        profile["user_id"] = user_id
        self.save_profile(user_id, profile)
        return profile

    def save_profile(self, user_id: str, profile: dict):
        path = self._file_path(user_id)
        profile["user_id"] = user_id
        # 清理已迁移到秋烨的旧字段
        profile.pop("loyalty", None)
        profile.pop("bond", None)
        profile.pop("today_fortune", None)
        profile.pop("fortune_date", None)
        profile.pop("modifications_left", None)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(profile, f, ensure_ascii=False, indent=2)

    def ensure_daily_reset(self, user_id: str, profile: dict) -> bool:
        today = _today_str()
        changed = False
        if profile.get("draw_date") != today:
            profile["drew_wife_today"] = False
            profile["wife_draw_count_today"] = 0
            profile["draw_date"] = today
            changed = True
        if profile.get("last_propose_date") != today:
            profile["proposed_today"] = False
            profile["proposed_to_today"] = None
            profile["last_propose_date"] = today
            changed = True
        if changed:
            self.save_profile(user_id, profile)
        return changed

    def record_draw(self, user_id: str):
        profile = self.get_profile(user_id)
        self.ensure_daily_reset(user_id, profile)
        is_first = not profile.get("drew_wife_today", False)
        if is_first:
            profile["drew_wife_today"] = True
        profile["wife_draw_count_today"] = profile.get("wife_draw_count_today", 0) + 1
        self.save_profile(user_id, profile)
        return profile, is_first, 0

    def record_propose(self, proposer_id: str, target_id: str):
        profile = self.get_profile(proposer_id)
        self.ensure_daily_reset(proposer_id, profile)
        today = _today_str()
        if not profile.get("proposed_today", False):
            profile["proposed_today"] = True
            profile["proposed_to_today"] = target_id
            profile["last_propose_date"] = today
        self.save_profile(proposer_id, profile)
        return profile, 0, []

    def can_propose(self, user_id: str):
        """求婚前置检查。返回 (可求婚, 羁绊占位, 拦截消息)。与原版语义一致：始终可求婚。"""
        return True, 0, ""

    def record_propose_accepted(self, context, bond_link, proposer_id: str, target_id: str):
        """求婚成功：双方羁绊 +5（bond 走秋烨），married_to 双向记录。"""
        proposer = self.get_profile(proposer_id)
        target = self.get_profile(target_id)
        proposer["married_to"] = target_id
        target["married_to"] = proposer_id
        self.save_profile(proposer_id, proposer)
        self.save_profile(target_id, target)
        b1 = bond_link.add_bond(context, proposer_id, 5)
        b2 = bond_link.add_bond(context, target_id, 5)
        return proposer, target, b1, b2, "求婚成功双方羁绊 +5"

    def update_yesterday_propose(self, user_id: str, target_id):
        profile = self.get_profile(user_id)
        today_target = profile.get("proposed_to_today")
        if today_target:
            profile["yesterday_proposed_to"] = today_target
        else:
            profile["yesterday_proposed_to"] = target_id
        self.save_profile(user_id, profile)

    # ============ COC 骰子判定（bond 由 hub_link 提供） ============

    def _coc_roll(self, skill: int) -> dict:
        roll = random.randint(1, 100)
        if roll <= 5:
            return {"roll": roll, "skill": skill, "level": 0, "label": "大成功"}
        if roll >= 96:
            return {"roll": roll, "skill": skill, "level": 5, "label": "大失败"}
        if roll <= skill // 5:
            return {"roll": roll, "skill": skill, "level": 1, "label": "极难成功"}
        if roll <= skill // 2:
            return {"roll": roll, "skill": skill, "level": 2, "label": "困难成功"}
        if roll <= skill:
            return {"roll": roll, "skill": skill, "level": 3, "label": "常规成功"}
        return {"roll": roll, "skill": skill, "level": 4, "label": "失败"}

    def _fortune_of(self, context, uid: str) -> int:
        """从秋烨读运势（读不到按 0）。"""
        try:
            f = context.get_registered_star("astrbot_plugin_qiuye").star_cls.get_fortune(uid)
            return int(f or 0)
        except Exception:
            return 0

    def _skill(self, context, bond_link, user_id: str, name: str = "") -> int:
        bond = bond_link.get_bond(context, user_id, name)
        fortune = self._fortune_of(context, user_id)
        return bond + fortune // 3

    def can_force_marry(self, context, bond_link, user_id: str, target_id: str, name: str = "") -> dict:
        bond = bond_link.get_bond(context, user_id, name)
        if bond < 20:
            return {"success": False, "blocked": True, "bond": bond, "reason": "羁绊不足"}
        fortune = self._fortune_of(context, user_id)
        skill = bond + fortune // 3
        target_bond = bond_link.get_bond(context, target_id)
        if target_bond <= 50:
            required, req_label = 3, "常规成功"
        elif target_bond <= 80:
            required, req_label = 2, "困难成功"
        else:
            required, req_label = 1, "极难成功"
        result = self._coc_roll(skill)
        success = full_success = False
        if result["level"] == 0:
            bond_link.add_bond(context, user_id, 10, name)
            success = full_success = True
        elif result["level"] == 5:
            bond_link.add_bond(context, user_id, -5, name)
        elif result["level"] <= required:
            success = True
        return {
            "success": success, "full_success": full_success, "blocked": False,
            "roll": result["roll"], "skill": skill, "level": result["level"],
            "label": result["label"], "req_label": req_label,
            "bond": bond, "fortune": fortune, "target_bond": target_bond,
            "is_crit_success": result["level"] == 0, "is_crit_fail": result["level"] == 5,
        }

    def can_force_marry_all(self, context, bond_link, user_id: str, name: str = "") -> dict:
        bond = bond_link.get_bond(context, user_id, name)
        if bond < 20:
            return {"success": False, "blocked": True, "bond": bond, "reason": "羁绊不足"}
        fortune = self._fortune_of(context, user_id)
        skill = bond + fortune // 3
        result = self._coc_roll(skill)
        success = result["level"] == 0
        is_crit_fail = result["level"] == 5
        if success:
            bond_link.add_bond(context, user_id, 10, name)
        elif is_crit_fail:
            bond_link.add_bond(context, user_id, -5, name)
        return {
            "success": success, "blocked": False,
            "roll": result["roll"], "skill": skill, "label": result["label"],
            "bond": bond, "fortune": fortune,
            "is_crit_success": success, "is_crit_fail": is_crit_fail,
        }

    def can_sever_ties(self, context, bond_link, user_id: str, name: str = "") -> dict:
        bond = bond_link.get_bond(context, user_id, name)
        if bond < 20:
            return {"success": False, "blocked": True, "bond": bond, "reason": "羁绊不足"}
        fortune = self._fortune_of(context, user_id)
        skill = bond + fortune // 3
        result = self._coc_roll(skill)
        success = full_success = False
        if result["level"] == 0:
            bond_link.add_bond(context, user_id, 10, name)
            success = full_success = True
        elif result["level"] == 5:
            bond_link.add_bond(context, user_id, -5, name)
        elif result["level"] <= 2:
            success = True
        return {
            "success": success, "full_success": full_success, "blocked": False,
            "roll": result["roll"], "skill": skill, "level": result["level"],
            "label": result["label"], "bond": bond, "fortune": fortune,
            "is_crit_success": result["level"] == 0, "is_crit_fail": result["level"] == 5,
        }

    def can_dian_yuanyang(self, context, bond_link, user_id: str, name: str = "") -> dict:
        bond = bond_link.get_bond(context, user_id, name)
        if bond < 20:
            return {"success": False, "blocked": True, "bond": bond, "reason": "羁绊不足"}
        fortune = self._fortune_of(context, user_id)
        skill = bond + fortune // 3
        result = self._coc_roll(skill)
        success = False
        if result["level"] == 0:
            bond_link.add_bond(context, user_id, 10, name)
            success = True
        elif result["level"] == 5:
            bond_link.add_bond(context, user_id, -5, name)
        elif result["level"] <= 2:
            success = True
        return {
            "success": success, "blocked": False,
            "roll": result["roll"], "skill": skill, "level": result["level"],
            "label": result["label"], "bond": bond, "fortune": fortune,
            "is_crit_success": result["level"] == 0, "is_crit_fail": result["level"] == 5,
        }

    def can_swap_bonds(self, context, bond_link, user_id: str, name: str = "") -> dict:
        bond = bond_link.get_bond(context, user_id, name)
        if bond < 20:
            return {"success": False, "blocked": True, "bond": bond, "reason": "羁绊不足"}
        fortune = self._fortune_of(context, user_id)
        skill = bond + fortune // 3
        result = self._coc_roll(skill)
        success = False
        if result["level"] == 0:
            bond_link.add_bond(context, user_id, 10, name)
            success = True
        elif result["level"] == 5:
            bond_link.add_bond(context, user_id, -5, name)
        elif result["level"] <= 1:
            success = True
        return {
            "success": success, "blocked": False,
            "roll": result["roll"], "skill": skill, "level": result["level"],
            "label": result["label"], "bond": bond, "fortune": fortune,
            "is_crit_success": result["level"] == 0, "is_crit_fail": result["level"] == 5,
        }

    def can_recall_past(self, context, bond_link, user_id: str, require_hard: bool = False, name: str = "") -> dict:
        bond = bond_link.get_bond(context, user_id, name)
        if bond < 20:
            return {"success": False, "blocked": True, "bond": bond, "reason": "羁绊不足"}
        fortune = self._fortune_of(context, user_id)
        skill = bond + fortune // 3
        result = self._coc_roll(skill)
        success = False
        if result["level"] == 0:
            bond_link.add_bond(context, user_id, 10, name)
            success = True
        elif result["level"] == 5:
            bond_link.add_bond(context, user_id, -5, name)
        elif result["level"] <= (3 if not require_hard else 2):
            success = True
        return {
            "success": success, "blocked": False,
            "roll": result["roll"], "skill": skill, "level": result["level"],
            "label": result["label"], "bond": bond, "fortune": fortune,
            "is_crit_success": result["level"] == 0, "is_crit_fail": result["level"] == 5,
        }
