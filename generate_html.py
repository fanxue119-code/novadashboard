#!/usr/bin/env python3
import json

# 读取 teachers_manual.json
with open("teachers_manual.json", "r", encoding="utf-8") as f:
    data = json.load(f)

teachers = data.get("teachers", [])

# 生成 HTML
html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>邮件跟踪</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            font-size: 11px;
            margin: 10px;
            background: #fff;
        }
        h1 {
            font-size: 16px;
            margin-bottom: 10px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 6px;
            text-align: left;
            vertical-align: top;
        }
        th {
            background: #f2f2f2;
            font-weight: bold;
        }
        .highlight { background: #fff9c4; }
        .name { font-weight: bold; }
        .small { font-size: 10px; color: #666; }
    </style>
</head>
<body>
    <h1>邮件跟踪</h1>
    <table>
        <thead>
            <tr>
                <th>老师</th>
                <th>邮箱</th>
                <th>类型</th>
                <th>阵容</th>
                <th>状态</th>
                <th>皮球</th>
                <th>邮件</th>
                <th>最后邮件</th>
                <th>最后行动</th>
                <th>价格</th>
                <th>沟通要点</th>
                <th>下一步</th>
            </tr>
        </thead>
        <tbody>
'''

for t in teachers:
    highlight = ' class="highlight"' if t.get('roster') == 'main' else ''
    
    # 价格
    cost = t.get('costDetails', {}).get('classes', {})
    price = cost.get('negotiatedRate', '') or cost.get('originalRate', '')
    
    # 沟通要点
    key_points = '<br>'.join(t.get('keyPoints', []))
    
    html += f'''            <tr{highlight}>
                <td class="name">{t.get('name', '')}</td>
                <td>{t.get('email', '')}</td>
                <td>{t.get('contactType', '')}</td>
                <td>{t.get('roster', '')}</td>
                <td>{t.get('status', '')}</td>
                <td>{t.get('ballSide', '')}</td>
                <td>{t.get('messageCount', 0)}</td>
                <td>{t.get('lastDate', '')}</td>
                <td>{t.get('lastAction', '')}<br><span class="small">{t.get('lastActionDate', '')}</span></td>
                <td>{price}</td>
                <td>{key_points}</td>
                <td><b>{t.get('nextAction', '')}</b><br><span class="small">{t.get('actionNote', '')}</span></td>
            </tr>
'''

html += '''        </tbody>
    </table>
</body>
</html>
'''

# 保存
with open("simple_tracking.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"已生成 simple_tracking.html，共 {len(teachers)} 位老师")
