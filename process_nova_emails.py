"""
Nova Email → Teacher CRM 处理脚本
用法: python3 process_nova_emails.py <threads目录> <输出json路径>

逻辑:
1. 读取所有 thread_meta.json + 对应 message json
2. 过滤无效thread（草稿/无回复/垃圾）
3. 按外部联系人邮箱聚合（一个人 = 一个老师条目）
4. 每个老师的所有邮件按时间排序，输出给AI提取
5. 写入结构化 JSON 供看板使用
"""

import os, json, re, glob
from datetime import datetime
from email.utils import parsedate_to_datetime

NOVA_EMAIL = "novadancecamp@gmail.com"

# ── 1. 读取所有thread ──────────────────────────────────────────────
def load_threads(threads_dir):
    threads = []
    for meta_path in glob.glob(os.path.join(threads_dir, "*", "thread_meta.json")):
        thread_dir = os.path.dirname(meta_path)
        with open(meta_path) as f:
            meta = json.load(f)

        # 读取每封邮件
        messages = []
        for msg_id in meta.get("messageIds", []):
            msg_path = os.path.join(thread_dir, f"{msg_id}.json")
            if os.path.exists(msg_path):
                with open(msg_path) as f:
                    messages.append(json.load(f))

        threads.append({"meta": meta, "messages": messages})

    return threads

# ── 2. 过滤无效thread ─────────────────────────────────────────────
def is_valid_thread(thread):
    meta = thread["meta"]
    messages = thread["messages"]

    # 过滤：只有Nova自己（无对方回复）
    participants = meta.get("participants", [])
    external = [p for p in participants if NOVA_EMAIL not in p]
    if not external:
        return False

    # 过滤：全是草稿
    all_draft = all("DRAFT" in m.get("labels", []) for m in messages if messages)
    if all_draft:
        return False

    # 过滤：垃圾subject
    subject = meta.get("subject", "").strip()
    if not subject or subject in ["111", "test", "测试"]:
        return False

    return True

# ── 3. 提取外部联系人邮箱 ─────────────────────────────────────────
def extract_email(raw):
    """从 'Name <email>' 或纯邮箱字符串提取邮箱"""
    m = re.search(r'<([^>]+)>', raw)
    if m:
        return m.group(1).lower().strip()
    return raw.lower().strip()

def get_external_email(thread):
    """从participants里找非Nova的邮箱"""
    for p in thread["meta"].get("participants", []):
        if NOVA_EMAIL not in p:
            return extract_email(p), p
    return None, None

# ── 4. 按联系人聚合 ───────────────────────────────────────────────
def aggregate_by_contact(threads):
    contacts = {}  # email -> {meta, messages}

    for thread in threads:
        if not is_valid_thread(thread):
            continue

        ext_email, ext_raw = get_external_email(thread)
        if not ext_email:
            continue

        if ext_email not in contacts:
            contacts[ext_email] = {
                "contact_email": ext_email,
                "contact_raw": ext_raw,
                "threads": [],
                "all_messages": []
            }

        contacts[ext_email]["threads"].append(thread["meta"])
        contacts[ext_email]["all_messages"].extend(thread["messages"])

    # 每个联系人的邮件按时间排序
    for email, data in contacts.items():
        data["all_messages"].sort(key=lambda m: parse_date(m.get("date", "")))

    return contacts

def parse_date(date_str):
    try:
        return parsedate_to_datetime(date_str)
    except:
        return datetime.min

# ── 5. 格式化给AI的邮件内容 ───────────────────────────────────────
def format_emails_for_ai(messages, max_messages=10):
    """取最近N封，格式化成易读文本"""
    recent = messages[-max_messages:]
    parts = []
    for i, msg in enumerate(recent, 1):
        date = msg.get("date", "unknown date")
        from_ = msg.get("from", "")
        body = msg.get("body", "").strip()

        # 截断过长的邮件body（引用历史邮件部分通常在---分隔符后）
        body = truncate_quoted_text(body)
        body = body[:2000]  # 最多2000字符/封

        direction = "← 对方发来" if NOVA_EMAIL not in from_ else "→ Nova发出"
        parts.append(f"[邮件{i} | {date} | {direction}]\n{body}")

    return "\n\n---\n\n".join(parts)

def truncate_quoted_text(body):
    """删除邮件引用的历史内容（On ... wrote: 之后的部分）"""
    patterns = [
        r'\nOn .+wrote:\n',
        r'\n-{3,}\nFrom:',
        r'\n_{3,}\n',
    ]
    for p in patterns:
        match = re.search(p, body, re.DOTALL)
        if match:
            body = body[:match.start()]
    return body

# ── 6. 构建AI提取prompt ───────────────────────────────────────────
EXTRACTION_PROMPT = """你是一个艺人合作信息提取助手，专门处理舞蹈老师的商务邮件。

以下是Nova Dance Camp与同一位联系人的所有往来邮件，按时间从旧到新排列。

【重要规则】
- 所有字段：若邮件中未明确出现，返回 null，严禁猜测或推断
- 报价字段：只提取明确出现的数字+币种，例如"$850 USD"→"850 USD"，不要四舍五入
- status判断：以最新邮件为准，只能从给定选项中选
- is_agent判断：只有当对方邮件中明确出现"I represent"/"on behalf of"/"I'm [姓名]'s manager/agent"等表述时才为true
- 邮件摘要：只描述最新一封邮件的核心内容，1-2句

【联系人基本信息】
- 联系邮箱: {contact_email}
- 邮件往来记录: 共{message_count}封

【需提取的字段】
返回以下JSON格式，不要添加任何解释文字：

{{
  "name": "老师全名（从邮件称呼或签名中提取）",
  "contact_email": "{contact_email}",
  "is_agent": false,
  "agent_name": null,
  "agent_email": null,
  "instagram": null,
  "nationality": null,
  "quote_original": null,
  "quote_negotiated": null,
  "quote_confirmed": null,
  "quote_currency": null,
  "status": "待联系|已发初始邮件|对方已回复|报价中|谈判中|已确认|已拒绝|失联",
  "declined_reason": null,
  "last_email_summary": "最新一封邮件的核心内容（1-2句）",
  "last_email_date": "最新邮件日期",
  "next_action": null,
  "notes": null
}}

【往来邮件内容】
{emails}
"""

# ── 7. 主流程 ─────────────────────────────────────────────────────
def process(threads_dir, output_path):
    print(f"读取threads目录: {threads_dir}")
    threads = load_threads(threads_dir)
    print(f"找到 {len(threads)} 个thread")

    contacts = aggregate_by_contact(threads)
    print(f"过滤后有效联系人: {len(contacts)} 个")

    # 输出每个联系人的提取任务
    results = []
    for email, data in contacts.items():
        emails_text = format_emails_for_ai(data["all_messages"])
        prompt = EXTRACTION_PROMPT.format(
            contact_email=email,
            message_count=len(data["all_messages"]),
            emails=emails_text
        )

        results.append({
            "contact_email": email,
            "thread_count": len(data["threads"]),
            "message_count": len(data["all_messages"]),
            "last_date": data["all_messages"][-1].get("date") if data["all_messages"] else None,
            "extraction_prompt": prompt,
            # 以下字段由AI填写
            "ai_extracted": None
        })

        print(f"  ✓ {email} | {len(data['threads'])}个thread | {len(data['all_messages'])}封邮件")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n输出: {output_path}")
    print(f"下一步: 对每条记录调用AI API，将结果写入 ai_extracted 字段")
    return results

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("用法: python3 process_nova_emails.py <threads目录> <输出json>")
        print("示例: python3 process_nova_emails.py ./threads ./teacher_tasks.json")
        sys.exit(1)

    process(sys.argv[1], sys.argv[2])
