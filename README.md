# Nova Email Archive

Nova Camp 老师邮件跟进系统

## 功能

- 从 Gmail API 拉取邮件存档
- 按老师分类整理邮件线程
- 用 Claude AI 自动提取老师信息（价格、状态等）
- 生成邮件跟踪表格

## 目录结构

```
nova_email_archive/
├── threads/                      # 原始邮件存档
│   ├── {threadId}/
│   │   └── messages/
│   │       └── *.json            # 每封邮件的完整JSON
├── process_nova_emails.py        # 第一步：整理邮件数据
├── extract_with_ai.py            # 第二步：用 Claude 提取信息
├── simple_tracking.html          # 邮件跟踪表格
├── API_SETUP.md                  # API 配置说明
└── .gitignore                    # Git 忽略文件
```

## 使用方法

### 环境准备

安装 Python 依赖：
```bash
pip3 install -r requirements.txt
```

### 1. 拉取邮件
配置 Gmail API（参考 `API_SETUP.md`），运行：
```bash
python3 pull_emails.py
```

### 2. 整理数据（第一步）
处理原始邮件，过滤无效内容，按联系人聚合：
```bash
python3 process_nova_emails.py ./threads ./teacher_tasks.json
```
输出：`teacher_tasks.json` - 每个联系人的提取任务

### 3. AI 提取（第二步）
用 Claude API 提取老师信息（需设置 `ANTHROPIC_API_KEY`）：
```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 extract_with_ai.py ./teacher_tasks.json ./teachers_crm.json
```
输出：`teachers_crm.json` - 结构化的老师信息

### 4. 生成表格
基于 CRM 数据生成 HTML 看板（可选）

## 关键改进

相比之前的脚本，新的两步流程解决了以下问题：

1. **过滤无效数据**：自动过滤草稿、无回复线程、垃圾邮件
2. **正确识别身份**：从 thread 的 participants 字段提取联系人，不依赖正文
3. **合并多线程**：同一老师的多个邮件线程会自动合并
4. **精准提取**：AI 提取时严格遵循规则，不猜测数据

## 隐私说明

此仓库仅包含代码和配置，**不包含**实际邮件内容和敏感信息。
