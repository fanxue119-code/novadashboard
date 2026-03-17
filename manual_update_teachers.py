#!/usr/bin/env python3
"""
手动更新关键老师的信息
"""

import json
from datetime import datetime

# 读取 teachers_manual.json
with open("teachers_manual.json", "r", encoding="utf-8") as f:
    manual_data = json.load(f)
    teachers = manual_data.get("teachers", [])

# 手动更新关键老师
manual_updates = {
    "Jordy": {
        "name": "Jordy Sparidaens",
        "email": "devon@capturethisams.com",  # 经纪人邮箱
        "contactType": "Agency Devon",
        "messageCount": 20,
        "threadId": "19beb0c249da44c9",
        "lastDate": "Thu, 5 Mar 2026",
        "pricesFromEmails": [],
        "roster": "second",
        "status": "婉拒",
        "ballSide": "己方",
        "keyPoints": [
            "Devon 拒绝了我们的最后报价",
            "你们决定用当前阵容，不再追求 Jordy"
        ],
        "nextAction": "已关闭",
        "actionNote": "Devon 回复说价格太低，你们决定放弃",
        "costDetails": {
            "classes": {
                "originalRate": "待确认",
                "negotiatedRate": "未达成一致"
            }
        }
    },
    "Robbie": {
        "name": "Robbie Blue",
        "email": "stevegaeto@blocagency.com",  # 经纪人 Steve
        "contactType": "Agency Bloc",
        "messageCount": 20,
        "threadId": "19c097adbe3de452",
        "lastDate": "Tue, 17 Mar 2026 08:47",
        "pricesFromEmails": [],
        "roster": "main",
        "status": "待签合同",
        "ballSide": "己方",
        "keyPoints": [
            "今早 Steve 回复接受了条款",
            "同意助理费 + out clause",
            "等待发正式合同"
        ],
        "nextAction": "今天发合同",
        "actionNote": "覆盖 Steve 确认的条款：助理费 + out clause",
        "costDetails": {
            "classes": {
                "count": 0,
                "originalRate": "待确认",
                "negotiatedRate": "已接受条款"
            }
        }
    },
    "Danny": {
        "name": "Daniel Wijngaarden",
        "email": "danieldwijngaarden@gmail.com",
        "contactType": "个人（大概率有 Agency）",
        "messageCount": 13,
        "threadId": "19beb10fa5235e1b",
        "lastDate": "Sun, 1 Feb 2026",
        "pricesFromEmails": ["650"],
        "roster": "backup",
        "status": "谈价中",
        "ballSide": "对方",
        "keyPoints": [
            "Danny 自己提价到 £850/class",
            "你们还价 £650/class",
            "等待 Danny 回复"
        ],
        "nextAction": "等待回复",
        "actionNote": "如果 Danny 接受 £650，可以作为 Backup",
        "costDetails": {
            "classes": {
                "count": 0,
                "originalRate": "£850/class",
                "negotiatedRate": "£650/class（我方还价）",
                "currency": "GBP",
                "unitPrice": 650
            }
        }
    },
    "Tina": {
        "name": "Tina Oleff (MSA Group)",
        "email": "Tina@msaagency.com",  # 或 info@msaagency.com
        "contactType": "Agency MSA",
        "messageCount": 20,
        "threadId": "待确认",
        "lastDate": "Fri, 13 Mar 2026",
        "pricesFromEmails": [],
        "roster": "main",
        "status": "谈价中",
        "ballSide": "对方",
        "keyPoints": [
            "昨夜发了 4-6 场 package 方案",
            "等待 MSA 回复"
        ],
        "nextAction": "等待回复",
        "actionNote": "跟进 4-6 场方案",
        "costDetails": {
            "classes": {
                "count": 0,
                "originalRate": "待确认",
                "negotiatedRate": "待确认"
            }
        }
    }
}

# 更新或添加老师
existing_names = {t["name"].lower() for t in teachers}

for key, update_data in manual_updates.items():
    # 查找是否已存在
    found = False
    for teacher in teachers:
        name = teacher["name"].lower()
        if key.lower() in name:
            # 更新现有老师
            teacher.update(update_data)
            found = True
            print(f"✅ 更新: {teacher['name']}")
            break
    
    if not found:
        # 添加新老师
        teachers.append(update_data)
        print(f"➕ 新增: {update_data['name']}")

# 更新其他老师的 roster
roster_updates = {
    "Rowan Chambers": "main",
    "Cassie Bartho": "main",
    "Pedro Reis": "backup",
    "BeauLexx": "dropped"
}

for teacher in teachers:
    name = teacher.get("name", "")
    for roster_name, roster_value in roster_updates.items():
        if roster_name.lower() in name.lower():
            teacher["roster"] = roster_value
            if roster_value != "未分类":
                print(f"✅ 更新阵容: {name} -> {roster_value}")

# 更新 manual_data
manual_data["teachers"] = teachers
manual_data["lastUpdated"] = datetime.now().strftime("%Y-%m-%d")

# 保存
with open("teachers_manual.json", "w", encoding="utf-8") as f:
    json.dump(manual_data, f, ensure_ascii=False, indent=2)

print()
print("✅ 手动更新完成！")
