#!/usr/bin/env python3
"""生成所有线程最后一封邮件的关键信息摘要，按邮件数量排序"""

import json
from pathlib import Path

threads_dir = Path("threads")

# 收集所有线程
thread_dirs = sorted([d for d in threads_dir.iterdir() if d.is_dir()])

# 收集线程信息
thread_info = []
for thread_dir in thread_dirs:
    thread_id = thread_dir.name
    msg_dir = thread_dir / "messages"
    msg_files = sorted(msg_dir.glob("*.json")) if msg_dir.exists() else []
    
    if msg_files:
        # 读取最后一封邮件
        with open(msg_files[-1], "r", encoding="utf-8") as f:
            last_msg = json.load(f)
        
        from_name = last_msg.get("from", "未知")
        date_str = last_msg.get("date", "")
        subject = last_msg.get("subject", "")
        body = last_msg.get("body", "")
        
        # 判断是否是系统邮件
        is_system = any(kw in from_name.lower() or kw in subject.lower() 
                       for kw in ['google', 'no-reply', 'noreply', 'community', 'accounts', 'security'])
        
        thread_info.append({
            'thread_id': thread_id,
            'count': len(msg_files),
            'from': from_name,
            'date': date_str,
            'subject': subject,
            'body': body[:350] if body else "",
            'is_system': is_system
        })

# 按邮件数量降序排序，非系统邮件优先
thread_info.sort(key=lambda x: (x['is_system'], -x['count']))

print("=" * 100)
print(f"共 {len(thread_info)} 个线程（按邮件数量排序，系统邮件置后）")
print("=" * 100)
print()

for i, t in enumerate(thread_info, 1):
    tag = "🔵" if not t['is_system'] else "🔘"
    print(f"{tag} #{i} 【{t['thread_id']}】({t['count']} 封邮件)")
    print(f"   日期: {t['date']}")
    print(f"   来自: {t['from']}")
    print(f"   主题: {t['subject'][:80]}...")
    print(f"   正文: {t['body']}...")
    print()
    print("-" * 100)
    print()
