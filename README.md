# astrbot_plugin_qiuhun（求婚）

从 autumn_blaze 拆出的**求婚系插件**：抽老婆/强娶/求婚全家族 + 群友羁绊档案与关系图。
羁绊（bond）与运势（fortune）统一存放于秋烨枢纽（astrbot_plugin_qiuye），本插件经 hub_link 读写；抽老婆候选池来自秋烨的活跃群友池。

## 依赖

| 插件 | 依赖方式 |
|---|---|
| [astrbot_plugin_qiuye](https://github.com/sfw2099/astrbot_plugin_qiuye)（秋烨枢纽） | 羁绊读写、运势读取、活跃池、使用记录。**未安装时降级**：bond 存本地 `bond_fallback.json`、活跃池为空 |

## 指令

| 指令 | 别名 | 说明 |
|---|---|---|
| 今日老婆 | 抽老婆 / jrlp | 从活跃群友池随机抽取今日老婆（每日限次） |
| 我的老婆 | 抽取历史 / wdlp | 查看今日抽取记录与剩余次数 |
| 强娶 `@某人` | qiangqu | COC 强娶判定（技能=羁绊+运势/3，难度随目标羁绊提升）；不@任何人=全体强娶（必须大成功），大成功也会升级为全体 |
| 斩红尘 `@某人` | zch | COC 判定斩断羁绊连线（可指定目标或斩自己全部） |
| 点鸳鸯 `@A @B` | dyy | COC 判定为两人牵线（可只@一人随机配对，或不@随机选两人） |
| 换连理 `@某人` | hll | COC 判定交换你与目标的全部羁绊连线（需极难成功） |
| 忆前世 `@某人` | ysq | 追忆昨日共同羁绊（不@则追忆自己昨日全部羁绊，需困难成功） |
| 求婚 `@某人` | qh | 发起求婚，对方 60 秒内回复「同意」接受；不@任何人=向全体求婚 |
| 关系图 `[N]` | gxt | 渲染群友老婆羁绊关系图（N=回溯天数，如 1 为昨天） |
| 个人关系图 | grgxt | 渲染以自己为中心的个人关系图 |
| 抽老婆帮助 | 老婆插件帮助 / clpbz | 帮助菜单 |
| 重置记录 | czjl | （管理员）清空今日抽取记录 |
| 重置次数 `<类型>` | czqqsj / czcs | （管理员）重置强娶/斩红尘/点鸳鸯/换连理/忆前世次数 |

> 支持关键词触发（无需 / 前缀），在插件配置中开启 `keyword_trigger_enabled`。

## COC 判定规则

- 技能值 = `羁绊 + 今日运势/3`（运势读自秋烨，未签到按 0）
- 1d100：≤5 大成功 / ≥96 大失败 / ≤技能/5 极难 / ≤技能/2 困难 / ≤技能 常规 / 否则失败
- 羁绊 <20 时强娶/斩红尘/点鸳鸯/换连理/忆前世直接被拦
- 大成功通常羁绊 +10，大失败羁绊 -5

## 数据布局

```
data/astrbot_plugin_qiuhun/
  records/{date}.json      # 每日婚姻/羁绊流水（抽老婆/强娶/求婚/点鸳鸯…），保留 30 天
  profiles/{uid}.json      # 求婚域档案（married_to/求婚状态/抽老婆计数）
  bond_fallback.json       # 秋烨未安装时的羁绊兜底存储
  temp/                    # 渲染图临时目录
```

## 从旧版 autumn_blaze 迁移（手动）

| 旧 | 新 |
|---|---|
| `autumn_blaze/records/` | `astrbot_plugin_qiuhun/records/`（整目录复制） |
| `autumn_blaze/forced_marriage.json` | `astrbot_plugin_qiuhun/`（整文件复制） |
| `autumn_blaze/profiles/` | `astrbot_plugin_qiuhun/profiles/`（整目录复制；`bond/today_fortune` 等旧字段加载后自动忽略） |
| `autumn_blaze/profiles/{uid}.json` 的 `bond` 值 | 并入秋烨 `users/{uid}.json` 的 `bond`（不迁则全员回 50，详见秋烨 README） |
| `autumn_blaze/group_fortune.json`、`active_users.json` | 归秋烨（见秋烨 README） |
