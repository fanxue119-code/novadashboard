#!/usr/bin/env python3
"""
Nova Dance Camp – Gmail 邮件完整存档脚本
每次运行：拉取所有 Nova 相关邮件线程，增量更新本地存档

存档结构：
  nova_email_archive/
    threads/
      <threadId>/
        thread_meta.json     # 线程元数据（发件人、主题、邮件数、最新日期）
        messages/
          <messageId>.json   # 每封邮件完整原始数据
    index.json               # 所有线程索引（快速查阅）
    last_sync.txt            # 上次同步时间
"""

import os
import json
import base64
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── 配置 ────────────────────────────────────────────────────────────────────
ARCHIVE_DIR = Path(__file__).parent
THREADS_DIR = ARCHIVE_DIR / "threads"
INDEX_FILE  = ARCHIVE_DIR / "index.json"
SYNC_FILE   = ARCHIVE_DIR / "last_sync.txt"

# 搜索关键词（OR 逻辑，尽量全覆盖）
SEARCH_QUERIES = [
    "Nova Dance Camp",
    "Teaching Invitation Nova",
    "Booking Inquiry Nova",
    "JueXing Project",
    "novadancecamp@gmail.com",
]

MAX_RESULTS = 500  # 每个查询最多拉取条数

# ── 工具函数 ─────────────────────────────────────────────────────────────────

def gws(params: dict) -> dict:
    """调用 gws CLI，返回解析后的 JSON"""
    cmd = ["gws", "gmail", "users", "messages", "get",
           "--params", json.dumps(params)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    raw = result.stdout.strip()
    # 过滤 keyring 警告行
    lines = [l for l in raw.splitlines() if not l.startswith("Using keyring")]
    try:
        return json.loads("\n".join(lines))
    except Exception:
        return {}


def gws_list(query: str, max_results: int = MAX_RESULTS) -> list:
    """列出符合条件的邮件（返回 [{id, threadId}, ...]）"""
    params = {"userId": "me", "q": query, "maxResults": max_results}
    cmd = ["gws", "gmail", "users", "messages", "list",
           "--params", json.dumps(params)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    raw = result.stdout.strip()
    lines = [l for l in raw.splitlines() if not l.startswith("Using keyring")]
    try:
        data = json.loads("\n".join(lines))
        return data.get("messages", [])
    except Exception:
        return []


def decode_body(payload: dict) -> str:
    """递归提取邮件纯文本正文"""
    mime = payload.get("mimeType", "")
    if mime == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            try:
                return base64.urlsafe_b64decode(data + "==").decode("utf-8", "ignore")
            except Exception:
                return ""
    for part in payload.get("parts", []):
        result = decode_body(part)
        if result:
            return result
    return ""


def get_header(headers: list, name: str) -> str:
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def parse_message(raw: dict) -> dict:
    """从原始 Gmail API 数据提取关键字段"""
    payload  = raw.get("payload", {})
    headers  = payload.get("headers", [])
    body_txt = decode_body(payload)

    return {
        "id":       raw.get("id", ""),
        "threadId": raw.get("threadId", ""),
        "from":     get_header(headers, "From"),
        "to":       get_header(headers, "To"),
        "cc":       get_header(headers, "Cc"),
        "date":     get_header(headers, "Date"),
        "subject":  get_header(headers, "Subject"),
        "labels":   raw.get("labelIds", []),
        "snippet":  raw.get("snippet", ""),
        "body":     body_txt,
        "raw":      raw,   # 保留完整原始数据
    }

# ── 主逻辑 ───────────────────────────────────────────────────────────────────

def fetch_all_message_ids() -> dict:
    """
    拉取所有 Nova 相关邮件 ID，去重后返回
    {messageId: threadId}
    """
    all_msgs = {}
    for q in SEARCH_QUERIES:
        print(f"  搜索: {q!r}")
        msgs = gws_list(q)
        for m in msgs:
            mid = m.get("id", "")
            tid = m.get("threadId", "")
            if mid:
                all_msgs[mid] = tid
        print(f"    → {len(msgs)} 封，累计 {len(all_msgs)} 封（去重）")
    return all_msgs


def load_existing_index() -> dict:
    if INDEX_FILE.exists():
        try:
            return json.loads(INDEX_FILE.read_text("utf-8"))
        except Exception:
            pass
    return {"threads": {}, "messages": {}}


def save_message(msg_data: dict):
    """将单封邮件存档到本地"""
    tid = msg_data["threadId"]
    mid = msg_data["id"]

    thread_dir  = THREADS_DIR / tid
    msg_dir     = thread_dir / "messages"
    msg_dir.mkdir(parents=True, exist_ok=True)

    msg_file = msg_dir / f"{mid}.json"
    msg_file.write_text(json.dumps(msg_data, ensure_ascii=False, indent=2), "utf-8")


def update_thread_meta(tid: str, index: dict):
    """根据已存档的邮件重新生成线程元数据"""
    thread_dir = THREADS_DIR / tid
    msg_dir    = thread_dir / "messages"

    if not msg_dir.exists():
        return

    messages = []
    for f in sorted(msg_dir.glob("*.json")):
        try:
            m = json.loads(f.read_text("utf-8"))
            messages.append(m)
        except Exception:
            pass

    if not messages:
        return

    # 按日期排序
    def parse_date(m):
        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(m["date"])
        except Exception:
            return datetime.min.replace(tzinfo=timezone.utc)

    messages.sort(key=parse_date)

    first = messages[0]
    last  = messages[-1]

    senders = list({m["from"] for m in messages if m["from"]})
    subjects = list({m["subject"] for m in messages if m["subject"]})
    subject = subjects[0] if subjects else ""

    meta = {
        "threadId":     tid,
        "subject":      subject,
        "messageCount": len(messages),
        "firstDate":    first["date"],
        "lastDate":     last["date"],
        "participants": senders,
        "lastSnippet":  last["snippet"],
        "messageIds":   [m["id"] for m in messages],
    }

    meta_file = thread_dir / "thread_meta.json"
    meta_file.write_text(json.dumps(meta, ensure_ascii=False, indent=2), "utf-8")

    # 更新全局 index
    index["threads"][tid] = {
        "threadId":     tid,
        "subject":      subject,
        "messageCount": len(messages),
        "lastDate":     last["date"],
        "participants": senders,
    }


def run():
    print(f"\n{'='*60}")
    print(f"Nova 邮件存档同步  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    THREADS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. 加载现有索引
    index = load_existing_index()
    existing_msgs = set(index.get("messages", {}).keys())
    print(f"已存档邮件数：{len(existing_msgs)}")

    # 2. 拉取全量 ID
    print("\n[1/4] 拉取 Nova 相关邮件 ID...")
    all_msgs = fetch_all_message_ids()
    new_ids = {mid: tid for mid, tid in all_msgs.items() if mid not in existing_msgs}
    print(f"\n共 {len(all_msgs)} 封邮件，其中新增 {len(new_ids)} 封需要下载")

    # 3. 下载新邮件
    if new_ids:
        print(f"\n[2/4] 下载 {len(new_ids)} 封新邮件...")
        failed = []
        for i, (mid, tid) in enumerate(new_ids.items(), 1):
            sys.stdout.write(f"\r  进度: {i}/{len(new_ids)}  ")
            sys.stdout.flush()
            raw = gws({"userId": "me", "id": mid, "format": "full"})
            if not raw or "id" not in raw:
                failed.append(mid)
                continue
            msg_data = parse_message(raw)
            save_message(msg_data)
            index["messages"][mid] = tid

        print(f"\n  ✅ 成功下载 {len(new_ids) - len(failed)} 封")
        if failed:
            print(f"  ⚠️  失败 {len(failed)} 封: {failed[:5]}")
    else:
        print("\n[2/4] 无新邮件，跳过下载")

    # 4. 更新所有线程元数据
    print("\n[3/4] 更新线程元数据...")
    all_thread_ids = set(all_msgs.values()) | set(
        d.name for d in THREADS_DIR.iterdir() if d.is_dir()
    )
    for tid in sorted(all_thread_ids):
        update_thread_meta(tid, index)
    print(f"  ✅ 已更新 {len(all_thread_ids)} 个线程")

    # 5. 保存全局索引
    print("\n[4/4] 保存索引...")
    INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False, indent=2), "utf-8")
    SYNC_FILE.write_text(datetime.now().isoformat(), "utf-8")

    # 6. 输出摘要
    total_threads = len(index.get("threads", {}))
    total_msgs    = len(index.get("messages", {}))
    print(f"\n{'='*60}")
    print(f"✅ 同步完成")
    print(f"   线程总数：{total_threads}")
    print(f"   邮件总数：{total_msgs}")
    print(f"   存档位置：{ARCHIVE_DIR}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run()
