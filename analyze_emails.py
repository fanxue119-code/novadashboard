#!/usr/bin/env python3
"""分析邮件线程，提取价格、邮件数等信息"""

import json
import re
from pathlib import Path

# 读取邮件线程数据
threads_dir = Path("threads")

results = []

for thread_dir in sorted(threads_dir.iterdir()):
    if not thread_dir.is_dir():
        continue
    
    thread_id = thread_dir.name
    messages_dir = thread_dir / "messages"
    
    if not messages_dir.exists():
        continue
    
    # 读取所有邮件
    messages = []
    for msg_file in messages_dir.glob("*.json"):
        try:
            msg_data = json.load(open(msg_file, 'r', encoding='utf-8'))
            messages.append(msg_data)
        except:
            continue
    
    if messages:
        # 按时间排序
        messages.sort(key=lambda x: x.get("internalDate", 0))
        
        # 提取信息
        result = {
            "threadId": thread_id,
            "messageCount": len(messages),
            "subject": messages[0].get("subject", ""),
            "fromEmails": [],
            "lastDate": messages[-1].get("date", ""),
            "lastFrom": messages[-1].get("from", "")
        }
        
        # 提取发送者邮箱
        for msg in messages:
            from_field = msg.get("from", "")
            from_match = re.search(r'<([^>]+)>', from_field)
            if from_match:
                email = from_match.group(1).lower().strip()
                if email not in result["fromEmails"]:
                    result["fromEmails"].append(email)
        
        # 提取价格信息
        prices = []
        for msg in messages:
            body = msg.get("body", "").lower()
            # 匹配价格格式：£/€/$ + 数字 + /class 或 /lesson
            price_patterns = [
                r'[£$€]\s*(\d+)\s*/\s*class',
                r'[£$€]\s*(\d+)\s*/\s*lesson',
                r'(\d+)\s*GBP\s*/\s*class',
                r'(\d+)\s*USD\s*/\s*class',
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, body)
                prices.extend(matches)
        
        result["prices"] = prices
        
        results.append(result)

# 输出结果
print("=" * 100)
print("邮件线程分析结果：")
print("=" * 100)
print()

for r in results:
    print(f"Thread: {r['threadId']}")
    print(f"  邮件数: {r['messageCount']}")
    print(f"  主题: {r['subject'][:80]}")
    print(f"  邮箱: {', '.join(r['fromEmails'][:5])}")
    print(f"  最后邮件: {r['lastDate']} | {r['lastFrom'][:50]}")
    if r['prices']:
        print(f"  价格: {', '.join(r['prices'][:5])}")
    print()
