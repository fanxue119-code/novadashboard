# NOVA Dance Camp 邮件归档系统 - API配置说明

## 📁 目录结构

```
nova_email_archive/
├── teachers_manual.json      # 手动维护的老师数据（状态、价格、沟通要点）
├── teachers.json             # 自动生成的邮件元数据（只读）
├── index.json                # 邮件线程索引
├── simple_tracking.html      # 邮件跟踪表（静态HTML）
├── threads/                  # 邮件存档目录（按线程分类）
│   ├── {thread_id_1}/
│   │   └── messages/
│   │       ├── {message_id_1}.json
│   │       ├── {message_id_2}.json
│   │       └── ...
│   ├── {thread_id_2}/
│   │   └── messages/
│   │       └── ...
│   └── ...
└── scripts/                  # 数据处理脚本
```

---

## 🔑 Gmail API 配置

### 1. 创建 Google Cloud 项目

1. 访问 https://console.cloud.google.com/
2. 创建新项目（或选择现有项目）
3. 启用 Gmail API：
   - 进入「API 和服务」→「库」
   - 搜索 "Gmail API"
   - 点击「启用」

### 2. 配置 OAuth 同意屏幕

1. 进入「API 和服务」→「OAuth 同意屏幕」
2. 选择「外部」用户类型
3. 填写必需信息：
   - 应用名称：`NOVA Dance Camp Email Archive`
   - 用户支持电子邮件：你的邮箱
   - 开发者联系信息：你的邮箱
4. 添加测试用户（添加你的 Gmail 账号）

### 3. 创建 OAuth 客户端

1. 进入「API 和服务」→「凭据」
2. 点击「创建凭据」→「OAuth 客户端 ID」
3. 应用类型选择：**桌面应用**
4. 名称：`Email Archive Client`
5. 点击「创建」
6. 下载客户端密钥文件（`client_secret_XXX.json`）

### 4. 安装依赖

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 5. 保存客户端密钥

将下载的 `client_secret_XXX.json` 放到项目目录，重命名为 `client_secret.json`

---

## 📧 邮件拉取脚本

### 首次运行（认证）

运行 `pull_emails.py` 进行首次认证：

```bash
python3 pull_emails.py
```

首次运行会：
1. 打开浏览器
2. 请求授权访问 Gmail
3. 访问成功后保存 `token.json`（以后无需重新认证）

### 自动拉取邮件

```bash
python3 pull_emails.py
```

脚本会：
1. 读取 `token.json` 获取访问令牌
2. 获取所有邮件线程
3. 下载邮件到 `threads/` 目录
4. 更新 `index.json` 和 `teachers.json`

### 定时任务（可选）

使用 cron 每天自动拉取邮件：

```bash
# 编辑 crontab
crontab -e

# 添加每天早上 9 点自动拉取
0 9 * * * cd /path/to/nova_email_archive && /usr/bin/python3 pull_emails.py >> email_pull.log 2>&1
```

---

## 📊 数据说明

### teachers_manual.json（手动维护）

这是**主要数据源**，手动维护老师的状态、价格、沟通要点。

```json
{
  "version": "1.2",
  "lastUpdated": "2026-03-17",
  "teachers": [
    {
      "name": "Rowan Chambers",
      "email": "chambersrowan@gmail.com",
      "contactType": "个人",
      "country": "英国",
      "roster": "main",           // 阵容: main/backup/second/dropped
      "status": "合同待发",       // 状态
      "ballSide": "己方",          // 皮球: 己/对/双
      "messageCount": 16,
      "lastDate": "Thu, 5 Mar 2026",
      "lastAction": "Rowan 回复 'you guys are amazing!'",
      "lastActionDate": "2026-03-15",
      "keyPoints": [              // 沟通要点（手动总结）
        "双方已口头完全达成一致",
        "Rowan 主动提出愿意接受 6 场保底"
      ],
      "nextAction": "今天发合同",  // 下一步行动
      "actionNote": "覆盖 2 场 Shanghai camp，注明 6 场保底条款",
      "costDetails": {
        "classes": {
          "count": 6,
          "originalRate": "£550/class",
          "negotiatedRate": "£550/class",
          "currency": "GBP",
          "unitPrice": 550,
          "totalTeachingFee": 3300
        },
        "flights": {
          "requirement": "商务舱直飞",
          "estimatedCost": 12000,
          "currency": "CNY"
        },
        "accommodation": {
          "roomType": "5星酒店",
          "nights": 4,
          "unitPricePerNight": 1200,
          "currency": "CNY",
          "total": 4800
        },
        "perDiem": {
          "amountPerDay": 70,
          "currency": "USD",
          "days": 4,
          "total": 280
        },
        "otherCosts": {
          "visaInsurance": 0,
          "transport": 0,
          "other": 0,
          "notes": ""
        }
      }
    }
  ]
}
```

### threads/（邮件存档）

每个线程一个文件夹，包含该线程的所有邮件：

```
threads/
└── 19beb0c249da44c9/
    └── messages/
        ├── 19beb0c249da44c9.json       # 第一封邮件
        ├── 19beb0d249da44c9.json       # 第二封邮件
        ├── 19beb0e249da44c9.json       # 第三封邮件
        └── ...
```

邮件 JSON 格式：

```json
{
  "id": "19beb0c249da44c9",
  "threadId": "19beb0c249da44c9",
  "from": "Devon Suriya <devon@capturethisams.com>",
  "to": "NOVA Dance Camp <novadancecamp@gmail.com>",
  "subject": "Re: Invitation to Join Nova Dance Camp",
  "date": "Fri, 23 Jan 2026 21:10:42 +0800",
  "internalDate": "1737630642000",
  "body": "邮件正文内容...",
  "snippet": "邮件预览...",
  "headers": {
    "From": "Devon Suriya <devon@capturethisams.com>",
    "To": "NOVA Dance Camp <novadancecamp@gmail.com>",
    "Subject": "Re: Invitation to Join Nova Dance Camp",
    "Date": "Fri, 23 Jan 2026 21:10:42 +0800"
  }
}
```

### index.json（线程索引）

记录所有线程和邮件的映射关系：

```json
{
  "version": "1.0",
  "lastUpdated": "2026-03-17T12:00:00Z",
  "totalThreads": 67,
  "totalMessages": 890,
  "threads": {
    "19beb0c249da44c9": {
      "id": "19beb0c249da44c9",
      "subject": "Re: Invitation to Join Nova Dance Camp",
      "messageCount": 20,
      "messages": [
        "19beb0c249da44c9",
        "19beb0d249da44c9",
        "19beb0e249da44c9",
        ...
      ]
    }
  }
}
```

### teachers.json（自动生成的邮件元数据）

从邮件自动提取的元数据（只读，不要手动编辑）：

```json
[
  {
    "name": "Jordy",
    "email": "devon@capturethisams.com",
    "roster": "second",
    "messageCount": 20,
    "negotiatedRate": "£550/class",
    "threadId": "19beb0c249da44c9"
  }
]
```

---

## 🛠️ 常用操作

### 1. 重新生成邮件跟踪表

更新 `teachers_manual.json` 后，重新生成静态 HTML：

```bash
python3 generate_html.py
```

### 2. 手动添加新老师

编辑 `teachers_manual.json`，在 `teachers` 数组中添加：

```json
{
  "name": "新老师姓名",
  "email": "teacher@email.com",
  "contactType": "个人",
  "country": "国家",
  "roster": "backup",
  "status": "未处理",
  "ballSide": "对方",
  "messageCount": 0,
  "lastDate": "",
  "lastAction": "",
  "lastActionDate": "",
  "keyPoints": [],
  "nextAction": "",
  "actionNote": "",
  "costDetails": {}
}
```

### 3. 从邮件提取价格信息

查看 `threads/{thread_id}/messages/` 目录，搜索关键词：
- `£/class`、`€/class`、`$/class`
- `per day`、`daily rate`
- `flight`、`airfare`
- `hotel`、`accommodation`

---

## ⚠️ 注意事项

1. **token.json** 包含访问令牌，**不要提交到 Git**
2. **client_secret.json** 包含 OAuth 客户端密钥，**不要提交到 Git**
3. **teachers_manual.json** 是主要数据源，手动维护
4. **teachers.json** 是自动生成的，不要手动编辑
5. 邮件拉取脚本会增量更新，不会重复下载已有邮件

---

## 📝 给其他 AI 的提示

如果你想给其他 AI（如 Claude、GPT-4）使用这个系统，可以这样描述：

```
我有一个 NOVA Dance Camp 邮件归档系统，包含以下文件：

1. teachers_manual.json - 手动维护的老师数据（状态、价格、沟通要点）
2. threads/ - 邮件存档（按线程分类，每封邮件一个JSON文件）
3. index.json - 邮件线程索引
4. simple_tracking.html - 邮件跟踪表（静态HTML）

请你：
1. 读取 teachers_manual.json 获取老师数据
2. 读取 threads/ 中的邮件文件，提取关键信息（价格、机酒要求等）
3. 更新 teachers_manual.json 中的字段（status、keyPoints、nextAction、costDetails）
4. 运行 generate_html.py 重新生成邮件跟踪表

主要任务：
- 从邮件中提取价格、机酒要求
- 总结沟通要点（keyPoints）
- 更新状态和下一步行动
```
