#!/usr/bin/env python3
"""
根据邮件线程分析结果更新 teachers_manual.json
"""

import json
import re
from pathlib import Path

# 读取邮件分析结果
email_analysis_file = "email_analysis.txt"
email_threads = {}

current_thread = None
with open(email_analysis_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line.startswith("Thread: "):
            current_thread = line.split(": ")[1]
            email_threads[current_thread] = {}
        elif current_thread and line.startswith("  邮件数: "):
            email_threads[current_thread]["messageCount"] = int(line.split(": ")[1])
        elif current_thread and line.startswith("  主题: "):
            email_threads[current_thread]["subject"] = line.split(": ", 1)[1]
        elif current_thread and line.startswith("  邮箱: "):
            email_threads[current_thread]["emails"] = [e.strip() for e in line.split(": ", 1)[1].split(",")]
        elif current_thread and line.startswith("  最后邮件: "):
            parts = line.split(" | ")
            date_part = parts[0].split(": ", 1)[1]
            from_part = parts[1] if len(parts) > 1 else ""
            email_threads[current_thread]["lastDate"] = date_part
            email_threads[current_thread]["lastFrom"] = from_part
        elif current_thread and line.startswith("  价格: "):
            prices = [p.strip() for p in line.split(": ", 1)[1].split(",")]
            email_threads[current_thread]["prices"] = prices

# 读取 teachers_manual.json
with open("teachers_manual.json", "r", encoding="utf-8") as f:
    manual_data = json.load(f)
    teachers = manual_data.get("teachers", [])

# 构建邮箱 -> 老师的映射
email_to_teacher = {}
for teacher in teachers:
    email = teacher.get("email", "").lower().strip()
    if email:
        email_to_teacher[email] = teacher

# 更新老师信息
for thread_id, thread_info in email_threads.items():
    if "emails" not in thread_info:
        continue
    
    # 遍历线程中的邮箱，找到对应的老师
    for email in thread_info["emails"]:
        email_lower = email.lower().strip()
        
        if email_lower in email_to_teacher:
            teacher = email_to_teacher[email_lower]
            
            # 更新邮件数
            if "messageCount" in thread_info:
                teacher["messageCount"] = thread_info["messageCount"]
            
            # 更新最后邮件时间
            if "lastDate" in thread_info:
                teacher["lastEmailDate"] = thread_info["lastDate"]
            
            # 更新价格信息
            if "prices" in thread_info and thread_info["prices"]:
                teacher["pricesFromEmails"] = thread_info["prices"]
                
                # 尝试解析价格
                if not teacher.get("costDetails"):
                    teacher["costDetails"] = {}
                if not teacher["costDetails"].get("classes"):
                    teacher["costDetails"]["classes"] = {}
                
                # 提取第一个价格
                price_str = thread_info["prices"][0]
                try:
                    price_num = int(price_str)
                    teacher["costDetails"]["classes"]["unitPrice"] = price_num
                    teacher["costDetails"]["classes"]["negotiatedRate"] = f"£{price_num}/class"
                except:
                    pass
            
            # 保存线程 ID
            teacher["threadId"] = thread_id
            
            print(f"✅ 更新 {teacher.get('name', '未知')}: 邮件数={thread_info.get('messageCount', 0)}, 价格={thread_info.get('prices', [])}")
            break

# 保存更新后的数据
manual_data["lastUpdated"] = "2026-03-17"
with open("teachers_manual.json", "w", encoding="utf-8") as f:
    json.dump(manual_data, f, ensure_ascii=False, indent=2)

print()
print("✅ 更新完成！")
