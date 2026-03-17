"""
用 Claude API 提取老师信息
用法: python3 extract_with_ai.py <teacher_tasks.json> <输出路径>
"""

import json, os, time
from anthropic import Anthropic

# 配置 Claude API
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    print("错误: 请设置环境变量 ANTHROPIC_API_KEY")
    print("示例: export ANTHROPIC_API_KEY=sk-ant-...")
    exit(1)

client = Anthropic(api_key=ANTHROPIC_API_KEY)

def extract_with_claude(prompt):
    """调用 Claude API 提取信息"""
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # 提取 JSON
        content = response.content[0].text.strip()

        # 清理可能的 markdown 代码块标记
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        return json.loads(content)
    except Exception as e:
        print(f"  ✗ 提取失败: {e}")
        return None

def process_tasks(tasks_path, output_path):
    """处理所有任务"""
    print(f"读取任务文件: {tasks_path}")

    with open(tasks_path, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    print(f"共 {len(tasks)} 个联系人待处理\n")

    results = []
    for i, task in enumerate(tasks, 1):
        email = task["contact_email"]
        prompt = task["extraction_prompt"]
        print(f"[{i}/{len(tasks)}] 处理 {email}...")

        # 调用 Claude 提取
        extracted = extract_with_claude(prompt)

        if extracted:
            task["ai_extracted"] = extracted
            print(f"  ✓ 成功提取: {extracted.get('name', '未知')}")
        else:
            print(f"  ✗ 提取失败，保持 null")
            task["ai_extracted"] = None

        results.append(task)

        # 避免限流，间隔 1 秒
        time.sleep(1)

        # 每 10 个保存一次进度
        if i % 10 == 0:
            save_progress(results, output_path)
            print(f"  → 已保存进度\n")

    # 最终保存
    save_progress(results, output_path)

    # 统计
    success_count = sum(1 for t in results if t["ai_extracted"] is not None)
    print(f"\n完成！成功提取 {success_count}/{len(results)} 个联系人")
    print(f"输出文件: {output_path}")

    return results

def save_progress(results, output_path):
    """保存当前进度"""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("用法: python3 extract_with_ai.py <teacher_tasks.json> <输出json>")
        print("示例: python3 extract_with_ai.py ./teacher_tasks.json ./teachers_crm.json")
        sys.exit(1)

    process_tasks(sys.argv[1], sys.argv[2])
