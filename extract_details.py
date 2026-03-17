#!/usr/bin/env python3
"""
深度解析邮件正文，提取关键业务信息

输入：threads/（邮件存档）
输出：更新 teachers.json（填充报价、条款、沟通进展等）
"""

import json
import re
from pathlib import Path
from datetime import datetime
from email.utils import parsedate_to_datetime

# 配置
ARCHIVE_DIR = Path(__file__).parent
THREADS_DIR = ARCHIVE_DIR / "threads"
TEACHERS_FILE = ARCHIVE_DIR / "teachers.json"
INDEX_FILE = ARCHIVE_DIR / "index.json"


def load_teachers():
    """加载现有老师数据"""
    with open(TEACHERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_index():
    """加载邮件索引"""
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_currency(text: str):
    """
    从文本中提取金额和货币
    返回: (amount, currency) 或 (None, None)
    """
    # 匹配模式：$1000, $1,000, £550, USD 1000
    patterns = [
        r'([$£€])(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
        r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(USD|GBP|EUR)',
        r'(USD|GBP|EUR)\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
    ]

    for pattern in patterns:
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        if matches:
            # 取第一个匹配
            m = matches[0].groupdict() if hasattr(matches[0], 'groupdict') else None
            if m:
                amount = float(m.get('amount') or m.get('currency') or 0)
                currency = m.get('currency') or m.get('symbol') or 'USD'
                # 清理符号
                amount = amount.replace(',', '').replace('$', '').replace('£', '').replace('€', '')
                return float(amount), currency.upper()
            else:
                # 简单模式，无命名组
                g = matches[0].groups()
                if g[0] in ['$', '£', '€']:
                    currency_map = {'$': 'USD', '£': 'GBP', '€': 'EUR'}
                    return float(g[1].replace(',', '')), currency_map[g[0]]
                else:
                    return float(g[1].replace(',', '')), g[0].upper()

    return None, None


def extract_rate_info(body: str, subject: str) -> dict:
    """提取报价信息"""
    rate = {
        "amount": 0,
        "currency": "USD",
        "minClasses": 0,
        "confirmedClasses": 0,
    }

    # 检查主题和正文中的金额
    for text in [subject, body]:
        amount, currency = parse_currency(text)
        if amount and amount > 0:
            rate["amount"] = max(rate["amount"], amount)
            rate["currency"] = currency

    # 提取最少场数
    min_match = re.search(r'min(?:imum)?\s*(\d+)\s*class', body, re.IGNORECASE)
    if min_match:
        rate["minClasses"] = int(min_match.group(1))

    # 提取已确认场数
    conf_match = re.search(r'(\d+)\s*class.*confirm', body, re.IGNORECASE)
    if conf_match:
        rate["confirmedClasses"] = int(conf_match.group(1))

    return rate


def extract_flights_hotel(body: str) -> dict:
    """提取机酒要求"""
    result = {
        "flights": {"required": False, "class": "Economy", "notes": ""},
        "hotel": {"required": False, "stars": 0, "nights": 0, "notes": ""},
        "perDiem": {"amount": 0, "currency": "USD", "days": 0},
    }

    # 机票
    if re.search(r'flight|airfare|ticket', body, re.IGNORECASE):
        result["flights"]["required"] = True
        if re.search(r'business\s*class', body, re.IGNORECASE):
            result["flights"]["class"] = "Business"
        elif re.search(r'economy\s*\+?', body, re.IGNORECASE):
            result["flights"]["class"] = "Economy Plus"

    # 酒店
    if re.search(r'hotel|accommodation|stay', body, re.IGNORECASE):
        result["hotel"]["required"] = True
        stars_match = re.search(r'(\d+)\s*star', body, re.IGNORECASE)
        if stars_match:
            result["hotel"]["stars"] = int(stars_match.group(1))

        nights_match = re.search(r'(\d+)\s*night', body, re.IGNORECASE)
        if nights_match:
            result["hotel"]["nights"] = int(nights_match.group(1))

    # Per diem
    pd_match = re.search(r'per\s*diem\s*(\d+)', body, re.IGNORECASE)
    if pd_match:
        result["perDiem"]["amount"] = int(pd_match.group(1))

    return result


def extract_shooting(body: str) -> dict:
    """提取拍摄授权信息"""
    result = {
        "allowed": None,
        "restrictions": [],
        "notes": ""
    }

    # 正向关键词
    positive = ['photo', 'video', 'film', 'shoot', 'record', 'capture']
    negative = ['no photo', 'no video', 'cannot', 'not allowed']

    if any(p in body.lower() for p in positive):
        if any(n in body.lower() for n in negative):
            result["allowed"] = False
            # 提取限制条件
            if 'no' in body.lower():
                restrictions = re.findall(r'no\s+(\w+)', body.lower())
                result["restrictions"] = restrictions
        else:
            result["allowed"] = True

    return result


def extract_timeline(messages: list) -> list:
    """
    从邮件序列中提取关键沟通节点
    返回: [{date, side, action, summary}, ...]
    """
    timeline = []

    # 关键词映射
    action_keywords = {
        'offer': '报价',
        'accept': '接受',
        'reject': '拒绝',
        'question': '询问',
        'confirm': '确认',
        'contract': '合同',
        'agreement': '协议',
        'payment': '付款',
        'schedule': '排课',
        'flight': '机票',
        'hotel': '酒店',
    }

    for msg in messages:
        try:
            date = parsedate_to_datetime(msg["date"])
            if date.tzinfo:
                date = date.replace(tzinfo=None)
        except:
            continue

        sender = msg.get("from", "").lower()
        body = msg.get("body", "").lower()

        # 判断哪一方
        side = "mine" if "novadancecamp" in sender else "theirs"

        # 提取动作
        action = "邮件沟通"
        for kw, act in action_keywords.items():
            if kw in body:
                action = act
                break

        # 提取摘要（取前100字）
        summary = msg.get("snippet", "")[:100]

        timeline.append({
            "date": date.strftime("%Y-%m-%d"),
            "side": side,
            "action": action,
            "summary": summary
        })

    # 按日期排序
    timeline.sort(key=lambda x: x["date"])
    return timeline


def extract_status(body: str, last_action: str) -> str:
    """从邮件内容推断状态"""
    body_lower = body.lower()

    # 紧急待处理
    if any(w in body_lower for w in ['send contract', 'issue contract', 'draft contract']):
        return "urgent"

    # 已签约
    if any(w in body_lower for w in ['signed', 'agreed', 'confirmed contract']):
        return "signed"

    # 等待对方
    if any(w in body_lower for w in ['looking forward', 'thanks', 'great', 'appreciate', 'let us know']):
        return "waiting"

    # 谈判中
    if any(w in body_lower for w in ['question', 'clarify', 'would like', 'proposal']):
        return "negotiate"

    # 放弃
    if any(w in body_lower for w in ['pass', 'decline', 'not possible', 'unfortunately']):
        return "dropped"

    return "waiting"


def determine_ball_side(body: str, sender: str) -> str:
    """判断球在哪边"""
    sender_lower = sender.lower()
    body_lower = body.lower()

    if "novadancecamp" in sender_lower:
        # Nova 的回复
        if any(w in body_lower for w in ['please let', 'we will', 'let me', 'waiting for']):
            return "theirs"
        else:
            return "mine"
    else:
        # 对方的回复
        if any(w in body_lower for w in ['will let', 'i will', "we'll", "i'll"]):
            return "mine"
        else:
            return "theirs"


def process_thread(thread_id: str, index: dict) -> dict:
    """
    处理单个线程，提取所有关键信息
    """
    thread_dir = THREADS_DIR / thread_id
    msg_dir = thread_dir / "messages"

    if not msg_dir.exists():
        return {}

    # 加载该线程的所有邮件
    messages = []
    for f in sorted(msg_dir.glob("*.json")):
        try:
            m = json.loads(f.read_text("utf-8"))
            messages.append(m)
        except:
            continue

    if not messages:
        return {}

    # 按日期排序
    messages.sort(key=lambda x: parsedate_to_datetime(x["date"]) if x.get("date") else datetime.min)

    # 获取最新邮件
    last_msg = messages[-1]
    last_body = last_msg.get("body", "")
    last_subject = last_msg.get("subject", "")
    last_sender = last_msg.get("from", "")

    # 提取各类信息
    rate = extract_rate_info(last_body, last_subject)
    expenses = extract_flights_hotel(last_body)
    shooting = extract_shooting(last_body)
    timeline = extract_timeline(messages)
    status = extract_status(last_body, "")
    ball_side = determine_ball_side(last_body, last_sender)

    # 生成下一步行动和摘要
    next_action = ""
    action_note = ""

    if "contract" in last_body.lower():
        if "send" in last_body.lower() or "issue" in last_body.lower():
            next_action = "等待发送合同"
        elif "sign" in last_body.lower():
            next_action = "等待签署合同"
    elif any(w in last_body.lower() for w in ['question', 'clarify']):
        next_action = "需要回复问题"
        action_note = "对方有疑问需要解答"
    elif any(w in last_body.lower() for w in ['accept', 'agree']):
        next_action = "准备合同"
    elif "looking forward" in last_body.lower():
        next_action = "等待对方进一步沟通"

    return {
        "rate": rate,
        "expenses": expenses,
        "shooting": shooting,
        "timeline": timeline,
        "status": status,
        "ballSide": ball_side,
        "nextAction": next_action,
        "actionNote": action_note,
    }


def run():
    print(f"\n{'='*60}")
    print("深度解析邮件内容")
    print(f"{'='*60}\n")

    # 加载数据
    teachers = load_teachers()
    index = load_index()

    print(f"老师数量: {len(teachers)}")
    print(f"线程数量: {len(index.get('threads', {}))}\n")

    # 处理每个老师对应的线程
    updated_count = 0
    for teacher in teachers:
        thread_id = teacher.get("id")
        if not thread_id:
            continue

        # 处理线程
        extracted = process_thread(thread_id, index)

        if extracted:
            # 更新老师数据
            teacher.update(extracted)
            updated_count += 1
            print(f"✅ {teacher.get('name', 'Unknown')}")

    # 保存更新后的数据
    with open(TEACHERS_FILE, "w", encoding="utf-8") as f:
        json.dump(teachers, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"✅ 完成！更新了 {updated_count} 位老师的信息")
    print(f"   文件: {TEACHERS_FILE}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run()
