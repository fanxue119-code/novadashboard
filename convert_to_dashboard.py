#!/usr/bin/env python3
"""
将邮件存档转换为看板数据格式（teachers.json）

输入：index.json（邮件存档索引）
输出：teachers.json（看板数据）
"""

import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

# 文件路径
ARCHIVE_DIR = Path(__file__).parent
INDEX_FILE = ARCHIVE_DIR / "index.json"
OUTPUT_FILE = ARCHIVE_DIR / "teachers.json"

# 已知老师信息映射（可根据实际情况补充）
TEACHER_MAPPING = {
    "rowan": {
        "name": "Rowan Chambers",
        "representative": "直接联系",
        "email": "chambersrowan@gmail.com",
        "roster": "main",
        "currency": "GBP",
        "rate": 550,
        "minClasses": 6,
    },
    "robbie": {
        "name": "Robbie (via Steve Gaeto)",
        "representative": "Bloc Agency · LA",
        "email": "stevegaeto@blocagency.com",
        "roster": "main",
        "currency": "USD",
        "rate": 0,  # 待确认
        "minClasses": 0,
    },
    "tina": {
        "name": "Tina Oleff (MSA Group)",
        "representative": "McDonald/Selznick Associates",
        "email": "Tina@msaagency.com",
        "roster": "main",
        "currency": "USD",
        "rate": 0,  # 因人而异
        "minClasses": 0,
    },
    "danny": {
        "name": "Danny Wijngaarden",
        "representative": "直接联系 · UK",
        "email": "danieldwijngaarden@gmail.com",
        "roster": "backup",
        "currency": "GBP",
        "rate": 833,  # £5000/6场
        "minClasses": 6,
    },
    "cassie": {
        "name": "Cassie Bartho (GiaNina)",
        "representative": "直接联系",
        "email": "contact@cassiebartho.com",
        "roster": "main",
        "currency": "USD",
        "rate": 1000,
        "minClasses": 0,
    },
    "pedro": {
        "name": "Pedro Reis",
        "representative": "Talitha Gonçalves · Pedro Reis Training",
        "email": "pedroreistraining@gmail.com",
        "roster": "backup",
        "currency": "USD",
        "rate": 1200,
        "minClasses": 3,
    },
    "preslee": {
        "name": "Preslee",
        "representative": "Annie Margolis · Clear Talent Group",
        "email": "annie@cleartalentgroup.com",
        "roster": "backup",
        "currency": "USD",
        "rate": 0,  # 待确认
        "minClasses": 0,
    },
    "sienna": {
        "name": "Sienna",
        "representative": "Carrie",
        "email": "",  # 待补充
        "roster": "backup",
        "currency": "USD",
        "rate": 0,
        "minClasses": 0,
    },
    "beaulexx": {
        "name": "Beaulexx",
        "representative": "直接联系",
        "email": "",
        "roster": "dropped",  # 持续无回复
        "currency": "USD",
        "rate": 0,
        "minClasses": 0,
    },
    "jordy": {
        "name": "Jordy",
        "representative": "Devon Suriya · Capture This AMS",
        "email": "devon@capturethisams.com",
        "roster": "second",  # 第二期
        "currency": "USD",
        "rate": 0,
        "minClasses": 0,
    },
}


def parse_date(date_str: str) -> datetime:
    """解析邮件日期，返回无时区 aware 日期"""
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str)
        # 去除时区信息，统一为无时区
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt
    except Exception:
        return datetime.min


def identify_teacher(thread: dict, all_msgs: List[dict]) -> dict:
    """
    根据线程参与者识别对应的老师

    优先级：TEACHER_MAPPING > 邮件发件人匹配
    """
    participants = thread.get("participants", [])
    subject = thread.get("subject", "").lower()

    # 先检查主题和参与者中的关键词
    keywords_map = {
        "rowan": ["rowan", "chambers"],
        "robbie": ["robbie", "steve", "bloc"],
        "tina": ["tina", "msa", "kimba", "kelly"],
        "danny": ["danny", "wijngaarden"],
        "cassie": ["cassie", "bartho", "gianina"],
        "pedro": ["pedro", "talitha"],
        "preslee": ["preslee", "annie"],
        "sienna": ["sienna", "carrie"],
        "beaulexx": ["beaulexx"],
        "jordy": ["jordy", "devon"],
    }

    for key, keywords in keywords_map.items():
        if key not in TEACHER_MAPPING:
            continue
        for kw in keywords:
            if kw in subject:
                return TEACHER_MAPPING[key]
            for p in participants:
                if kw in p.lower():
                    return TEACHER_MAPPING[key]

    # 默认返回空模板
    return {
        "name": thread.get("subject", "")[:50] or "未知老师",
        "representative": "",
        "email": "",
        "roster": "backup",
        "currency": "USD",
        "rate": 0,
        "minClasses": 0,
    }


def infer_status(thread: dict, all_msgs: List[dict]) -> str:
    """
    根据最新邮件推断状态

    返回：urgent | waiting | signed | negotiate | dropped
    """
    last_snippet = thread.get("lastSnippet", "").lower()
    last_date = parse_date(thread.get("lastDate", ""))
    days_since = (datetime.now() - last_date).days

    # 关键词判断
    if any(w in last_snippet for w in ["contract", "agreement", "signed"]):
        return "signed"
    if days_since > 14:
        return "dropped"
    if any(w in last_snippet for w in ["looking forward", "thanks", "great", "accept"]):
        return "waiting"
    if any(w in last_snippet for w in ["question", "clarify", "how", "what", "would"]):
        return "negotiate"

    # 默认等待
    return "waiting"


def infer_ball_side(thread: dict, all_msgs: List[dict]) -> str:
    """
    判断球在哪边

    返回：mine | theirs | both
    """
    last_snippet = thread.get("lastSnippet", "").lower()
    if any(w in last_snippet for w in ["we will", "i will", "we'll", "i'll", "let me"]):
        return "theirs"
    if any(w in last_snippet for w in ["looking forward", "thanks", "please let", "would love"]):
        return "mine"
    return "both"


def convert():
    """主转换逻辑"""
    if not INDEX_FILE.exists():
        print(f"❌ 找不到索引文件：{INDEX_FILE}")
        print("请先运行 fetch_nova_emails.py 拉取邮件")
        return

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        index = json.load(f)

    threads = index.get("threads", {})
    print(f"找到 {len(threads)} 个线程")

    teachers = []

    for tid, thread_info in threads.items():
        teacher = identify_teacher(thread_info, [])
        status = infer_status(thread_info, [])
        ball_side = infer_ball_side(thread_info, [])

        teachers.append({
            "id": tid,
            "name": teacher["name"],
            "representative": teacher["representative"],
            "email": teacher["email"],
            "roster": teacher["roster"],

            "status": status,
            "statusText": {
                "urgent": "🔴 紧急待处理",
                "waiting": "🟡 等待对方",
                "signed": "✅ 已签约",
                "negotiate": "🔵 谈判中",
                "dropped": "⚪ 已放弃",
            }[status],

            "ballSide": ball_side,

            "lastAction": thread_info.get("lastSnippet", "")[:100],
            "lastActionDate": thread_info.get("lastDate", ""),
            "messageCount": thread_info.get("messageCount", 0),

            "rate": {
                "amount": teacher["rate"],
                "currency": teacher["currency"],
                "minClasses": teacher["minClasses"],
            },

            # 预留字段，后续手动补充
            "expenses": {
                "flights": {},
                "hotel": {},
                "perDiem": {},
            },
            "specialRequirements": [],
            "shooting": {
                "allowed": None,
                "restrictions": [],
            },
            "timeline": [],
        })

    # 保存输出
    OUTPUT_FILE.write_text(
        json.dumps(teachers, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"✅ 转换完成！")
    print(f"   输出文件：{OUTPUT_FILE}")
    print(f"   老师数量：{len(teachers)}")

    # 统计
    from collections import Counter
    roster_counts = Counter(t["roster"] for t in teachers)
    print(f"\n阵容分布：")
    for r, c in roster_counts.items():
        print(f"  {r}: {c}")


if __name__ == "__main__":
    convert()
