#!/usr/bin/env python3
import json

with open("teachers.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 系统邮件关键词过滤
skip_keywords = [
    "your account is live",
    "google account",
    "set up your google",
    "confirm your account",
    "verify your",
    "security alert",
    "sign-in attempt",
    "password reset",
    "instagram",
    "play.google",
    "googlecommunity",
    "no-reply",
    "noreply",
]

valid_teachers = []
for t in data:
    name_lower = t["name"].lower()
    subject_lower = name_lower

    valid_keywords = [
        "rowan", "robbie", "steve", "bloc", "tina", "msa", "kimba",
        "kelly", "danny", "cassie", "gianina", "pedro", "talitha",
        "preslee", "annie", "sienna", "carrie", "beaulexx", "jordy", "devon",
    ]

    if any(kw in name_lower for kw in valid_keywords):
        valid_teachers.append(t)
    elif any(kw in subject_lower for kw in skip_keywords):
        continue
    elif not t["representative"] and not t["email"]:
        continue
    else:
        valid_teachers.append(t)

print(f"原始数据: {len(data)}")
print(f"过滤后: {len(valid_teachers)}")

with open("teachers.json", "w", encoding="utf-8") as f:
    json.dump(valid_teachers, f, ensure_ascii=False, indent=2)

print("\n已覆盖原文件 teachers.json")

from collections import Counter
roster_counts = Counter(t["roster"] for t in valid_teachers)
print("\n阵容分布：")
for r, c in roster_counts.items():
    print(f"  {r}: {c}")
