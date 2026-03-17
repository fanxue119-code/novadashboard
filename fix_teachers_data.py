#!/usr/bin/env python3
"""
数据校对和修复脚本：
1. 从 Excel 读取准确的老师信息（邮箱、类型）
2. 从邮件线程读取邮件数和价格
3. 合并到 teachers_manual.json
"""

import json
import re
from pathlib import Path
from collections import defaultdict

# 读取 Excel 数据
excel_data = json.load(open('/tmp/nova_contact_data.json', 'r', encoding='utf-8'))
excel_header = excel_data[0]

# 构建邮箱 -> 老师信息的映射
excel_by_email = {}
excel_by_name = {}

for row in excel_data[1:]:
    if len(row) < 9:
        continue
    
    name = row[2] if len(row) > 2 else ""
    email = row[8] if len(row) > 8 else ""
    contact_type = row[9] if len(row) > 9 else ""
    stage = row[6] if len(row) > 6 else ""
    progress = row[3] if len(row) > 3 else ""
    country = row[7] if len(row) > 7 else ""
    
    if email:
        email = email.lower().strip()
        excel_by_email[email] = {
            "name": name,
            "email": email,
            "contactType": contact_type,
            "stage": stage,
            "progress": progress,
            "country": country
        }
    
    if name:
        excel_by_name[name.lower().strip()] = {
            "name": name,
            "email": email,
            "contactType": contact_type,
            "stage": stage,
            "progress": progress,
            "country": country
        }

# 读取邮件分析结果
email_threads = {}
current_thread = None
with open("email_analysis.txt", 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line.startswith("Thread: "):
            current_thread = line.split(": ")[1]
            email_threads[current_thread] = {}
        elif current_thread and line.startswith("  邮件数: "):
            email_threads[current_thread]["messageCount"] = int(line.split(": ")[1])
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

# 读取现有的 teachers_manual.json
try:
    with open("teachers_manual.json", "r", encoding="utf-8") as f:
        manual_data = json.load(f)
        existing_teachers = manual_data.get("teachers", [])
except:
    manual_data = {"version": "1.2", "lastUpdated": "2026-03-17", "teachers": []}
    existing_teachers = []

# 邮箱 -> 老师映射（用于更新邮件信息）
email_to_teacher = {}

# 匹配老师信息
print("=" * 100)
print("数据校对结果：")
print("=" * 100)
print()

matched_teachers = []

for teacher in existing_teachers:
    name = teacher.get("name", "")
    
    excel_info = None
    
    # 先尝试名字匹配
    for excel_name, info in excel_by_name.items():
        if excel_name in name.lower():
            excel_info = info
            break
    
    if excel_info:
        # 更新老师信息
        teacher["name"] = excel_info["name"]
        teacher["email"] = excel_info["email"]
        teacher["contactType"] = excel_info["contactType"]
        teacher["stage"] = excel_info["stage"]
        teacher["progress"] = excel_info["progress"]
        teacher["country"] = excel_info["country"]
        
        matched_teachers.append(teacher)
        if excel_info["email"]:
            email_to_teacher[excel_info["email"].lower()] = teacher
        
        print(f"✅ 匹配: {teacher['name']} | {excel_info['email']}")
    else:
        print(f"⚠️  未找到 Excel 匹配: {name}")
        matched_teachers.append(teacher)

# 查找有邮件但没有在 matched_teachers 里的老师
print()
print("从邮件中查找新老师...")
print()

for thread_id, thread_info in email_threads.items():
    if "emails" not in thread_info:
        continue
    
    # 尝试通过邮箱匹配
    for email in thread_info["emails"]:
        email_lower = email.lower().strip()
        
        if email_lower in excel_by_email:
            excel_info = excel_by_email[email_lower]
            # 检查是否已经在列表里
            found = False
            for teacher in matched_teachers:
                if teacher.get("email", "").lower().strip() == email_lower:
                    # 更新邮件信息
                    teacher["messageCount"] = thread_info.get("messageCount", 0)
                    teacher["threadId"] = thread_id
                    teacher["lastSubject"] = thread_info.get("subject", "")
                    teacher["lastDate"] = thread_info.get("lastDate", "")
                    
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
                    
                    found = True
                    break
            
            if not found:
                # 新建老师记录
                new_teacher = {
                    "name": excel_info["name"],
                    "email": excel_info["email"],
                    "contactType": excel_info["contactType"],
                    "stage": excel_info["stage"],
                    "progress": excel_info["progress"],
                    "country": excel_info["country"],
                    "messageCount": thread_info.get("messageCount", 0),
                    "threadId": thread_id,
                    "lastSubject": thread_info.get("subject", ""),
                    "lastDate": thread_info.get("lastDate", ""),
                    "roster": "未分类",
                    "status": "未处理",
                    "ballSide": "对方",
                    "keyPoints": [],
                    "nextAction": "",
                    "actionNote": "",
                    "costDetails": {}
                }
                
                # 更新价格信息
                if "prices" in thread_info and thread_info["prices"]:
                    new_teacher["pricesFromEmails"] = thread_info["prices"]
                    try:
                        price_num = int(thread_info["prices"][0])
                        new_teacher["costDetails"]["classes"] = {
                            "unitPrice": price_num,
                            "negotiatedRate": f"£{price_num}/class"
                        }
                    except:
                        pass
                
                matched_teachers.append(new_teacher)
                email_to_teacher[email_lower] = new_teacher
                print(f"➕ 新增老师（来自邮件）: {excel_info['name']} ({excel_info['email']}) | 邮件数: {thread_info.get('messageCount', 0)}")
            break

# 输出匹配结果
print()
print("=" * 100)
print(f"共 {len(matched_teachers)} 位老师")
print("=" * 100)
print()
print(f"{'姓名':<30} {'邮箱':<35} {'类型':<12} {'阶段':<12} {'进度':<8} {'邮件数':<6}")
print("=" * 100)

for t in sorted(matched_teachers, key=lambda x: x.get("messageCount", 0), reverse=True):
    print(f"{t['name']:<30} {t.get('email', ''):<35} {t.get('contactType', ''):<12} {t.get('stage', ''):<12} {t.get('progress', ''):<8} {t.get('messageCount', 0):<6}")

# 更新 manual_data
manual_data["teachers"] = matched_teachers
manual_data["lastUpdated"] = "2026-03-17"

# 保存到文件
with open("teachers_manual.json", "w", encoding="utf-8") as f:
    json.dump(manual_data, f, ensure_ascii=False, indent=2)

print()
print("✅ 数据校对完成！已保存到 teachers_manual.json")
