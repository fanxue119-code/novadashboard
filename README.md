# Nova Email Archive

Nova Camp 老师邮件跟进系统

## 功能

- 从 Gmail API 拉取邮件存档
- 按老师分类整理邮件线程
- 生成邮件跟踪表格
- 提取邮件中的关键信息（价格、状态、沟通要点等）

## 目录结构

```
nova_email_archive/
├── threads/                      # 原始邮件存档
│   ├── {threadId}/
│   │   └── messages/
│   │       └── *.json            # 每封邮件的完整JSON
├── teachers_manual.json          # 老师手动数据（价格、状态等）
├── thread_index.json             # 线程索引
├── message_index.json            # 邮件索引
├── pull_emails.py                # 从 Gmail 拉取邮件
├── simple_tracking.html          # 邮件跟踪表格
├── API_SETUP.md                  # API 配置说明
└── .gitignore                    # Git 忽略文件
```

## 使用方法

1. 配置 Gmail API（参考 `API_SETUP.md`）
2. 运行 `python3 pull_emails.py` 拉取邮件
3. 编辑 `teachers_manual.json` 添加老师信息
4. 生成 HTML 表格查看进度

## 隐私说明

此仓库仅包含代码和配置，**不包含**实际邮件内容和敏感信息。
