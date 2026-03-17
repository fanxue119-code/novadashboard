# NOVA Dance Camp 邮件跟进系统 - 数据说明

## 📁 文件结构

```
nova_email_archive/
├── teachers_manual.json      ← 手动维护的状态和沟通要点（主要数据源）
├── teachers.json             ← 自动生成的邮件数据（只读，不要手动编辑）
├── email_dashboard.html       ← 邮件跟进表页面（主要查看入口）
├── threads/                  ← 邮件存档（按线程分类）
├── index.json                ← 邮件索引
└── scripts/                  ← 数据处理脚本
```

## 📊 数据分工

### 自动数据（teachers.json）
- **邮件数**：自动统计每个线程的邮件数量
- **最后邮件时间**：自动提取最后邮件的日期
- **价格信息**：从邮件正文提取价格（如 £650/class）
- **机酒要求**：从邮件提取住宿、机票要求

### 手动数据（teachers_manual.json）
- **status**：当前状态（待签合同、谈价中、婉拒等）
- **ballSide**：球在哪边（己/对/双）
- **keyPoints**：沟通要点（人工总结）
- **nextAction**：下一步行动（具体待办）
- **actionNote**：行动备注（细节说明）
- **roster**：阵容分类（main/backup/second/dropped）
- **costDetails**：结构化费用明细

## ✅ 已校对的数据

### 主要老师（已核对）

| 老师 | 邮件数 | 阵容 | 状态 | 报价 | 说明 |
|---|---|---|---|---|---|
| **Rowan Chambers** | 16 | main | 待签合同 | £550/class | 已口头一致，等待发合同 |
| **Robbie Blue** | 20 | main | 待签合同 | 已接受条款 | 今早 Steve 接受，等待发合同 |
| **Tina Oleff (MSA)** | 20 | main | 谈价中 | 待确认 | 昨夜发 4-6 场方案 |
| **Daniel Wijngaarden** | 13 | backup | 谈价中 | £650/class（还价） | Danny 要 £850，我们还价 £650 |
| **Jordy Sparidaens** | 20 | second | 婉拒 | 未达成 | Devon 拒绝，已放弃 |
| **BeauLexx** | 10 | dropped | 谈价中 | 待确认 | 10 封邮件，已放弃 |
| **Cassie Bartho** | 10 | main | 待签合同 | £1000/class | 直接联系 Cassie（非 GiaNina） |
| **Pedro Reis** | 12 | backup | 谈价中 | 待确认 | 通过 Talitha 联系 |

### 其他老师

以下老师也在 `teachers_manual.json` 中，但邮件数较少或联系未深入：

- Yasmina (Jena) - 5 封邮件 - 对未来合作开放，本届阵容已满
- Sveta - 5 封邮件 - 婉拒
- Colette - 5 封邮件 - 感谢兴趣，春节放假中

## 🎯 使用方式

### 查看邮件跟进表

```bash
# 在浏览器中打开
open email_dashboard.html

# 或用本地服务器（支持自动刷新）
python3 -m http.server 8000
# 然后访问 http://localhost:8000/email_dashboard.html
```

### 更新状态和沟通要点

直接编辑 `teachers_manual.json`：

```json
{
  "name": "Rowan Chambers",
  "roster": "main",
  "status": "合同待发",
  "ballSide": "己方",
  "keyPoints": [
    "双方已口头完全达成一致",
    "Rowan 主动提出愿意接受 6 场保底"
  ],
  "nextAction": "今天发合同",
  "actionNote": "覆盖 2 场 Shanghai camp，注明 6 场保底条款"
}
```

### 更新阵容

在 `email_dashboard.html` 页面中，直接点击「阵容」下拉框调整：
- **本期主阵容** (main)
- **Backup** (backup)
- **第二期** (second)
- **已放弃** (dropped)

### 邮件数据同步

每天早上 9 点自动拉取新邮件，邮件数和价格信息自动更新，无需手动干预。

## ⚠️ 注意事项

1. **Robbie Blue vs GiaNina**：
   - Robbie 的经纪人是 Steve (stevegaeto@blocagency.com)
   - Cassie Bartho 是直接联系（contact@cassiebartho.com）
   - GiaNina 是另一位老师，不是 Cassie 的经纪人

2. **Jordy Sparidaens**：
   - 经纪人是 Devon (devon@capturethisams.com)
   - 已婉拒，阵容改为「第二期」

3. **Daniel Wijngaarden**：
   - 自己提价到 £850/class
   - 我们还价 £650/class（邮件里写的是 £650）
   - **注意**：不是 £800

4. **Pedro Reis**：
   - 通过经纪人的 Talitha 联系
   - 邮件里应该有我们砍价的信息

## 🔍 数据验证

### 如何核对邮件数据

1. 打开 `email_dashboard.html` 查看
2. 检查「邮件数」和「最后邮件时间」是否正确
3. 如需查看邮件原文，进入 `threads/` 目录查看对应线程

### 如何验证价格信息

1. 查看 `teachers_manual.json` 中的 `pricesFromEmails` 字段
2. 进入 `threads/{threadId}/messages/` 查看邮件正文
3. 搜索价格关键词（£/€/$ + 数字 + /class）

## 📝 后续改进

### 待完成功能

1. **前端编辑保存**：点击「下一步行动」可编辑并保存到 `teachers_manual.json`
   - 需要后端支持（Python Flask 或 Node.js）

2. **自动提取费用**：从邮件提取更完整的费用信息
   - 机票要求（经济舱/商务舱）
   - 住宿要求（酒店级别、间数）
   - 每日津贴金额

3. **邮件提醒**：
   - 超过 X 天未回复的老师高亮
   - 自动发送跟进提醒

4. **历史记录**：记录每次状态变更的时间和历史

---

**最后更新时间**: 2026-03-17
**数据版本**: v1.2
