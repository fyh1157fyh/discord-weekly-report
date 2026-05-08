from __future__ import annotations

import re

from .models import AnalyzedPost, CollectedPost
from .scoring import heat_score


CATEGORY_KEYWORDS = [
    ("活动玩法", "竞技场/决斗", ["arena", "duel", "champion", "ava"]),
    ("赛季机制", "迁服", ["migration", "transfer", "state transfer", "迁服", "转服"]),
    ("活动玩法", "峡谷", ["canyon", "canyon clash", "峡谷"]),
    ("活动玩法", "火山战", ["volcano", "lava", "火山"]),
    ("活动玩法", "荣耀战", ["honor battle", "honor", "荣耀"]),
    ("奖励建议", "奖励内容", ["reward", "rewards", "奖励"]),
    ("系统优化", "匹配机制", ["matchmaking", "match", "matching", "匹配"]),
]

EXACT_TITLE_TRANSLATIONS = {
    "voting in group chats": "群聊投票功能",
    "seasonal building relocations/placements qol": "赛季建筑迁移和摆放优化",
    "how come we don't have tank skins, i'd like to see my tank in camouflage, just asking.": "坦克缺少迷彩皮肤",
    "game expasion": "扩展游戏内容",
    "buster day teleports": "Buster Day 迁城体验",
    "free teleport on sat regardless of whether duel opponent is on same or different server": "统一周六决斗免费迁城",
    "harassment": "骚扰问题反馈",
    "lost point": "积分丢失问题",
    "warehouse boxes": "仓库箱子相关建议",
    "210% discount on gold bars": "金条折扣显示异常",
    "treasure dig reward realignment proposal": "宝藏挖掘奖励调整建议",
    "please add shopeepay as a payment method on the website.": "官网支付接入 ShopeePay",
    "levels should give more formation power.": "提升等级对应编队战力",
    "overburdened report lists": "战报列表负担过重",
    "create a blind auction": "新增盲拍玩法",
    "canyon communication": "峡谷玩法沟通体验",
    "ban auto clickers on digs": "挖掘玩法应禁止连点器",
    "adding more hospitals": "增加医院数量",
    "merger": "服务器合并建议",
    "fuel pass": "燃油通行证建议",
    "clothes shop tickets": "服装商店券建议",
    "email change for multiple characters": "多角色邮箱更换需求",
    "friendly challenge": "友谊挑战功能",
    "clickable links in mails!": "邮件链接希望可点击",
    "upgrade issue": "升级异常问题",
    "glory wars is horrible": "荣耀战体验较差",
    "radar gas cost!": "雷达燃油消耗过高",
    "power cores in helicopter treasure": "直升机宝藏希望产出能量核心",
    "flags including": "国旗内容补充建议",
    "buster kill day": "Buster 击杀日体验",
    "end of season 3 exchange": "第三赛季结束兑换建议",
    "bug": "Bug 问题反馈",
    "the badges problem (and some suggestions_solutions)": "徽章问题及改进建议",
    "stackable shielding!": "护盾支持叠加",
    "alliance chat recap with time period & smart filters": "联盟聊天回顾和智能筛选",
    "random teleport button on world screen": "世界界面随机迁城按钮",
    "make some more events like canyon clash": "增加峡谷类活动",
    "add cores-forging stones and item to upgrato to d5 inside digs": "挖掘加入核心和 D5 升级材料",
    "fair play – ban auto-clickers for helicopter treasures": "直升机宝藏应禁止连点器",
    "autocorrect implemented in game typing": "聊天输入希望加入自动纠错",
    "digs! big holes! tesouro!": "挖掘玩法体验建议",
    "calendar and gas": "日历和燃油相关建议",
    "reset card to reset the stars of our refugees": "增加难民星级重置卡",
    "trade hub - 2 times slots for different timezones": "贸易中心支持不同时区档期",
    "compensation for vip levels": "VIP 等级补偿建议",
    "make the wrenchs less rare in the wandering trader": "流浪商人扳手刷新过少",
    "update for resources output/h": "每小时资源产量显示更新",
    "allow the alliances r5 to export duel own results": "R5 导出决斗结果",
    "plugins": "插件功能建议",
    "we need faster soldier building": "士兵训练速度过慢",
    "hopefully": "死州合服需求",
    "setting to remove drag to march": "关闭拖拽行军设置",
    "free teleport when fighting same server alliances": "同服联盟对战免费迁城",
    "협곡쟁탈전": "峡谷争夺战反馈",
    "a building to make switching equipment between formations and heroes easier": "新增建筑便捷切换装备",
    "unfair disadvantage for ungrouped states and attackers": "未分组州和进攻方存在不公平劣势",
    "add more fuel": "增加燃油获取",
    "pulse module": "脉冲模块建议",
    "pc version needs a update for uploading avatar": "PC 端支持上传头像",
    "removing inactive players": "长期不活跃玩家处理建议",
    "método de pago paypal web oficial": "官网支付希望支持 PayPal",
    "hero skill and experience reset": "英雄技能和经验重置建议",
    "compensation scam weekly pack": "每周礼包补偿争议",
    "remove truck shares": "移除卡车分享",
    "increase amount of blue decoration chests": "增加蓝色装饰箱数量",
    "seeing the messages someone replies to": "查看被回复的原消息",
    "warehouse protection": "仓库保护建议",
    "reward": "奖励相关建议",
    "please make an open state where we can just rumble any time.": "开放可随时战斗州",
    "in game support option": "游戏内客服入口建议",
    "season 5?": "第五赛季相关询问",
    "fuel sharing": "燃油共享建议",
    "treasure digs.": "宝藏挖掘建议",
    "there needs to be changes to soldiers / units.": "士兵和单位需要调整",
    "chat system": "聊天系统建议",
    "for country flags": "国家旗帜建议",
    "warrior battle pass based on faction": "按阵营设计勇士战令",
    "troops stuck in canyon clash": "峡谷争夺中部队卡住",
    "svs 135 vs 153": "SVS 匹配 135 对 153 反馈",
    "canyon": "峡谷玩法反馈",
    "eu friendly reset timing": "EU 玩家反馈重置时间不友好",
    "ava points and al stuff used for mod vevical": "AvA 积分和载具材料未计入",
    "gift": "增加礼包赠送功能",
    "add fuel to the shop": "商店增加燃油",
    "suggestions for players to manually adjust gold bar payment to their local currency.": "金条支付支持手动切换本地货币",
    "new hq skins": "新增总部皮肤",
    "show 0 contributors in alliance rankings": "联盟排行显示零贡献成员",
    "auto translation in chat": "聊天自动翻译",
    "things the game needs": "玩家汇总的功能需求",
    "same server vs opponent teleports": "同服对战迁城规则反馈",
    "headquarter decoration for women": "增加女性向总部装饰",
    "migrating starter hqs": "初始总部迁移建议",
    "state ruler rework": "重做州长系统",
    "add upi as a payment method on website": "官网支付支持 UPI",
    "add electric engine!!!!": "增加电动引擎",
    "roses": "增加玫瑰内容",
    "alliance squad management feature": "新增联盟小队管理",
    "unable to attack in arena before server reset, missed my chance to get better daily, weekly rewards": "Arena 重置前无法攻击导致错过奖励",
    "speed ups": "增加加速道具",
    "please actually start taking action against people like this": "希望官方处理违规玩家",
    "tyrant bug after volcano event": "火山活动后暴君 Bug",
    "rallies": "优化集结玩法",
    "⛽🛢️ fuel": "燃油资源建议",
    "frame for lucky discounter , and lucky shot is so ugly": "幸运折扣和幸运射击外观较差",
    "auto-help record": "新增自动帮助记录",
    "time zone and event days": "活动日期和时区安排建议",
    "whales 🐳": "大 R 玩家影响反馈",
    "vip streaks need adjustment": "VIP 连续奖励需要调整",
    "random selection system": "优化随机选择系统",
    "add hindi language support in auto translation": "自动翻译希望支持印地语",
    "track hq in alliance": "联盟内追踪总部位置",
    "rss share between alliance members & more ways to collect wrenches": "联盟资源共享与扳手获取",
    "auto zooming": "自动缩放问题反馈",
    "during buster day, we should be able to reinforce other hqs of the same server": "Buster Day 希望可支援同服总部",
    "migration slots": "迁服名额建议",
    "last z tos update ⛔ & migration controversy😱 – what’s really happening?": "服务条款更新和迁服争议",
    "tradehub teleport issue": "贸易中心迁城问题",
    "game expansion": "游戏内容扩展建议",
    "ex destroyer": "EX Destroyer 相关反馈",
    "bugg": "Bug 问题反馈",
}


TITLE_PATTERNS = [
    (["gift"], "希望增加礼物功能"),
    (["clusters", "balanced"], "集群平衡和官方干预争议"),
    (["lag", "issues"], "游戏长期卡顿问题"),
    (["game", "freezes"], "游戏卡死并重启问题"),
    (["tvt", "point", "manipulation"], "TvT 刷 EB 分机制问题"),
    (["merger", "state", "dead"], "死州合服需求"),
    (["fuel", "shop"], "希望商店增加燃油"),
    (["manually"], "希望玩家可以手动操作相关功能"),
    (["new", "hq", "skin"], "希望增加新的总部皮肤"),
    (["auto translation", "chat"], "希望聊天支持自动翻译"),
    (["headquarter decoration", "women"], "希望增加女性向总部装饰"),
    (["state ruler", "rework"], "希望重做州长系统"),
    (["upi", "payment"], "希望官网支付支持 UPI"),
    (["electric engine"], "希望增加电动引擎"),
    (["roses"], "希望增加玫瑰相关内容"),
    (["speed ups"], "希望增加加速道具"),
    (["taking action"], "希望官方实际处理玩家反馈"),
    (["voting", "group chat"], "希望群聊支持投票功能"),
    (["ava", "lost"], "AvA 积分或载具材料未计入"),
    (["ava", "glitch"], "AvA 积分或载具材料未计入"),
    (["reset", "eu"], "EU 玩家反馈重置时间不友好"),
    (["unable", "attack", "arena"], "Arena 重置前无法攻击"),
    (["free teleport", "same server"], "同服联盟决斗缺少免费迁城"),
    (["export", "duel", "results"], "希望导出 Duel 对战结果"),
    (["alliance squad management"], "希望增加联盟小队管理功能"),
    (["fuel", "pass"], "希望增加燃油周卡/月卡"),
    (["avatar", "pc"], "PC 端希望支持上传头像"),
    (["inactive players"], "希望优化长期不活跃玩家处理"),
    (["alliance rankings", "zero contributions"], "联盟排行希望显示零贡献成员"),
    (["trade system"], "希望增加联盟资源交易系统"),
    (["move resources"], "希望增加联盟资源交易系统"),
    (["radars", "not counted"], "Duel 雷达事件未计数"),
    (["migration"], "迁服规则或成本相关反馈"),
    (["transfer"], "迁服规则或成本相关反馈"),
    (["reward"], "奖励获得感相关反馈"),
    (["bug"], "疑似异常导致玩家损失"),
    (["unable"], "疑似异常导致玩家损失"),
    (["lost"], "疑似异常导致玩家损失"),
]


WORD_TRANSLATIONS = {
    "gift": "礼物",
    "gifts": "礼物",
    "fuel": "燃油",
    "shop": "商店",
    "new": "新增",
    "hq": "总部",
    "headquarter": "总部",
    "headquarters": "总部",
    "skin": "皮肤",
    "skins": "皮肤",
    "decoration": "装饰",
    "decorations": "装饰",
    "women": "女性",
    "female": "女性",
    "auto": "自动",
    "automatic": "自动",
    "translation": "翻译",
    "translate": "翻译",
    "chat": "聊天",
    "state": "州",
    "ruler": "州长",
    "rework": "重做",
    "upi": "UPI",
    "payment": "支付",
    "method": "方式",
    "website": "网站",
    "electric": "电动",
    "engine": "引擎",
    "roses": "玫瑰",
    "rose": "玫瑰",
    "speed": "加速",
    "ups": "道具",
    "suggestions": "建议",
    "suggestion": "建议",
    "players": "玩家",
    "player": "玩家",
    "manually": "手动",
    "manual": "手动",
    "action": "处理",
    "taking": "执行",
    "actually": "真正",
    "start": "开始",
    "please": "",
    "add": "增加",
    "allow": "允许",
    "show": "显示",
    "remove": "移除",
    "removing": "移除",
    "feature": "功能",
    "request": "请求",
    "better": "优化",
    "mailbox": "邮箱",
    "mail": "邮件",
    "sorting": "排序",
    "sort": "排序",
    "filters": "筛选",
    "filter": "筛选",
}


def analyze_posts_locally(posts: list[CollectedPost]) -> list[AnalyzedPost]:
    return [_analyze_post(post) for post in posts]


def _analyze_post(post: CollectedPost) -> AnalyzedPost:
    text = _post_text(post)
    primary, secondary = _classify(text)
    return AnalyzedPost(
        post=post,
        short_title=_chinese_title(post),
        summary=_chinese_summary(post),
        primary_category=primary,
        secondary_category=secondary,
        sentiment_score=_sentiment_score(text, post.reaction_stats.negative),
        heat_score=heat_score(post),
    )


def _classify(text: str) -> tuple[str, str]:
    for primary, secondary, keywords in CATEGORY_KEYWORDS:
        if any(keyword.casefold() in text for keyword in keywords):
            return primary, secondary
    return "未分类", "待人工确认"


def _chinese_title(post: CollectedPost) -> str:
    text = _post_text(post)
    exact = EXACT_TITLE_TRANSLATIONS.get(_normalize_title(post.title))
    if exact:
        return _polish_issue_title(exact)
    for keywords, title in TITLE_PATTERNS:
        if all(keyword in text for keyword in keywords):
            return _polish_issue_title(title)
    return _polish_issue_title(_fallback_chinese_title(post.title, post.starter_content))


def _chinese_summary(post: CollectedPost) -> str:
    title = _chinese_title(post)
    text = _post_text(post)
    source = _source_excerpt(post)
    if title == "群聊投票功能":
        return "玩家希望在群聊中增加投票功能，方便联盟或队伍内部做决策。"
    if title == "集群平衡和官方干预争议":
        return "玩家质疑集群平衡和官方干预方式，认为服务器或个人被定向影响，公平感受到破坏。"
    if title in {"游戏长期卡顿问题", "游戏卡死并重启问题"}:
        return "玩家反馈游戏在宝藏等场景中频繁卡顿、断线或重启，影响抢资源和正常参与。"
    if title == "TvT 刷 EB 分机制问题":
        return "玩家反馈联盟通过 TvT 长时间刷 EB 分且几乎没有损失，破坏真实 PvP 和排行榜竞争。"
    if title == "死州合服需求":
        return "玩家反馈部分州因迁服后人数流失严重，建议通过合服恢复活跃度。"
    if title.endswith("建议") or title.endswith("反馈") or title.endswith("需求"):
        return f"玩家提出“{title}”，需要结合原帖场景判断影响范围和优先级。"
    if title.startswith("希望"):
        return f"玩家{title[2:]}。"
    if title.startswith("AvA"):
        return "玩家反馈 AvA 相关积分或载具材料因疑似故障未计入，影响活动积分结算，需要核对日志。"
    if title.startswith("EU"):
        return "玩家反馈服务器重置时间落在欧洲凌晨 3/4 点，影响 AvA 冲分和活动参与体验。"
    if "无法攻击" in title:
        return "玩家反馈重置前无法在 Silver/Peak Arena 发起攻击，因此错过每日或每周奖励机会。"
    if "免费迁城" in title:
        return "玩家认为同服联盟决斗也应该提供免费迁城，否则与跨服对手规则不一致。"
    if "联盟排行" in title:
        return "玩家希望联盟排行显示零贡献成员，便于管理者识别未参与贡献的成员。"
    if "迁服" in title:
        return f"玩家提出迁服相关反馈，关注点可能是规则、资格、道具或成本。原文摘录：{source}"
    if "奖励" in title:
        return f"玩家提出奖励相关反馈，重点关注投入产出、奖励缺口或结算损失。原文摘录：{source}"
    if "异常" in title or "损失" in title:
        return f"玩家反馈疑似异常导致无法参与、进度丢失或奖励损失。原文摘录：{source}"
    if "bug" in text or "unable" in text or "lost" in text:
        return f"玩家反馈疑似异常导致无法参与、进度丢失或奖励损失。原文摘录：{source}"
    return f"玩家提出“{title}”相关建议，建议结合原帖场景评估优先级。原文摘录：{source}"


def _fallback_chinese_title(title: str, body: str) -> str:
    cleaned = " ".join((title or body).strip().split())
    if not cleaned:
        return "未命名建议"
    if not _is_mostly_ascii(cleaned):
        return cleaned[:40]
    translated = _translate_english_words(f"{cleaned} {body}")
    if translated:
        return translated
    return "功能体验优化"


def _polish_issue_title(title: str) -> str:
    replacements = {
        "希望增加": "增加",
        "希望新增": "新增",
        "希望优化": "优化",
        "希望支持": "支持",
        "希望关闭": "关闭",
        "希望移除": "移除",
        "希望官方": "官方",
        "玩家建议：": "",
        "相关建议": "建议",
        "相关反馈": "反馈",
        "体验较差": "体验差",
        "排序增加筛选": "排序筛选",
    }
    result = title
    for source, target in replacements.items():
        result = result.replace(source, target)
    return result[:40]


def _normalize_title(title: str) -> str:
    return " ".join(title.strip().casefold().split())


def _translate_english_words(text: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", text.casefold())
    translated: list[str] = []
    for word in words:
        value = WORD_TRANSLATIONS.get(word)
        if value and value not in translated:
            translated.append(value)
    return "".join(translated)[:32]


def _source_excerpt(post: CollectedPost, limit: int = 120) -> str:
    source = post.starter_content.strip() or post.title.strip()
    cleaned = " ".join(source.split())
    if not cleaned:
        return "该帖暂无可读正文，需要查看原帖。"
    return cleaned if len(cleaned) <= limit else cleaned[: limit - 1].rstrip() + "..."


def _post_text(post: CollectedPost) -> str:
    return " ".join([post.title, post.starter_content, " ".join(post.conversation)]).casefold()


def _is_mostly_ascii(text: str) -> bool:
    if not text:
        return False
    ascii_count = sum(1 for char in text if ord(char) < 128)
    return ascii_count / len(text) > 0.8


def _sentiment_score(text: str, negative_reactions: int) -> int:
    score = 5 + min(negative_reactions, 3)
    if any(word in text for word in ["unfair", "bad", "bug", "impossible", "不公平", "问题"]):
        score += 2
    return max(1, min(score, 10))
